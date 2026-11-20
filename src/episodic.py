"""Episodic Recall Trace & Offline Sleep Consolidation Engine."""

import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple

from src.vector_index import FastVectorIndex, STOP_WORDS, _WORD_RE


def _topic_signature(text: str, intent: str) -> str:
    words = [w for w in _WORD_RE.findall((text or "").lower()) if w not in STOP_WORDS and len(w) > 2]
    key_words = sorted(set(words))[:4]
    if not key_words:
        return f"{intent}:general"
    return f"{intent}:" + "_".join(key_words)


class EpisodicMemory:
    """Tracks every interaction turn (input, recall path, output, feedback)
    and periodically consolidates raw episodes into compact reusable schemas."""

    def __init__(self, max_raw_episodes: int = 180):
        self.max_raw_episodes = max_raw_episodes
        self.episodes: List[Dict[str, Any]] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.last_consolidation_at: float = 0.0
        self.total_consolidated_episodes: int = 0
        self.index = FastVectorIndex(dim=256, max_hot_items=2000)

    def _index_episode(self, ep: Dict[str, Any]) -> None:
        eid = ep.get("id", "")
        if not eid:
            return
        blob = f"{ep.get('user_input', '')} {ep.get('response', '')} {ep.get('intent', '')}"
        self.index.add(eid, blob)

    def record(
        self,
        user_input: str,
        intent: str,
        recalled_frame_ids: List[str],
        proof_steps: List[str],
        response: str,
        confidence: float,
        mode: str,
    ) -> Dict[str, Any]:
        now = time.time()
        raw_sig = f"{now}|{user_input[:64]}|{len(self.episodes)}"
        eid = "ep_" + hashlib.blake2b(raw_sig.encode("utf-8"), digest_size=5).hexdigest()

        ep = {
            "id": eid,
            "timestamp": now,
            "user_input": (user_input or "")[:400],
            "intent": intent or "chat",
            "topic_sig": _topic_signature(user_input, intent or "chat"),
            "recalled_frame_ids": list(recalled_frame_ids)[:20],
            "proof_steps": list(proof_steps)[:8],
            "response": (response or "")[:500],
            "confidence": round(float(confidence), 3),
            "mode": mode or "unknown",
            "feedback": "neutral",
            "consolidated": False,
        }
        self.episodes.append(ep)
        self._index_episode(ep)

        # Auto-trigger lightweight consolidation if raw log crosses threshold
        if len(self.episodes) > self.max_raw_episodes:
            self.consolidate(force=False)

        return ep

    def get_last_episode(self, skip_meta: bool = True) -> Optional[Dict[str, Any]]:
        for ep in reversed(self.episodes):
            if skip_meta and ep.get("intent") in {"meta_recall", "feedback_positive", "feedback_negative"}:
                continue
            return ep
        return self.episodes[-1] if self.episodes else None

    def mark_last_feedback(self, feedback: str) -> Optional[Dict[str, Any]]:
        ep = self.get_last_episode(skip_meta=True)
        if not ep:
            return None
        ep["feedback"] = feedback
        return ep

    def recall_similar(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.22,
    ) -> List[Tuple[Dict[str, Any], float]]:
        hits = self.index.search(query, top_k=top_k, min_score=min_score)
        ep_by_id = {ep["id"]: ep for ep in self.episodes}
        results: List[Tuple[Dict[str, Any], float]] = []
        for eid, score in hits:
            ep = ep_by_id.get(eid)
            if ep:
                results.append((ep, score))
        return results

    def consolidate(self, force: bool = True) -> Dict[str, Any]:
        """Offline Sleep Consolidation: cluster recurring episodes into abstract schemas
        and prune redundant old raw logs so memory stays fast and sharp."""
        now = time.time()
        unconsolidated = [ep for ep in self.episodes if not ep.get("consolidated")]
        if not force and len(unconsolidated) < 12:
            return {"schemas_created": 0, "schemas_updated": 0, "pruned": 0}

        clusters: Dict[str, List[Dict[str, Any]]] = {}
        for ep in unconsolidated:
            sig = ep.get("topic_sig") or _topic_signature(ep.get("user_input", ""), ep.get("intent", "chat"))
            clusters.setdefault(sig, []).append(ep)

        created = 0
        updated = 0
        for sig, group in clusters.items():
            # Require at least 2 matching episodes (or 1 explicit positive feedback) to distill a schema
            has_pos = any(g.get("feedback") == "positive" for g in group)
            if len(group) < 2 and not has_pos:
                continue

            sch_id = "sch_" + hashlib.blake2b(sig.encode("utf-8"), digest_size=5).hexdigest()
            avg_conf = sum(float(g.get("confidence", 0.5)) for g in group) / max(1, len(group))
            frame_ids: List[str] = []
            for g in group:
                for fid in g.get("recalled_frame_ids", []):
                    if fid not in frame_ids:
                        frame_ids.append(fid)

            sample_input = group[-1].get("user_input", "")[:140]
            sample_resp = group[-1].get("response", "")[:160]

            if sch_id in self.schemas:
                sch = self.schemas[sch_id]
                sch["support_count"] = int(sch.get("support_count", 1)) + len(group)
                sch["confidence"] = round((float(sch.get("confidence", 0.5)) + avg_conf) / 2.0, 3)
                sch["linked_frame_ids"] = list(dict.fromkeys(sch.get("linked_frame_ids", []) + frame_ids))[:25]
                sch["latest_example"] = f"Q: {sample_input} -> A: {sample_resp}"
                sch["updated_at"] = now
                updated += 1
            else:
                self.schemas[sch_id] = {
                    "id": sch_id,
                    "pattern_key": sig,
                    "support_count": len(group),
                    "confidence": round(avg_conf, 3),
                    "linked_frame_ids": frame_ids[:25],
                    "latest_example": f"Q: {sample_input} -> A: {sample_resp}",
                    "created_at": now,
                    "updated_at": now,
                }
                created += 1

            for g in group:
                g["consolidated"] = True
                self.total_consolidated_episodes += 1

        # Prune oldest consolidated episodes if exceeding raw budget (never lose recent context)
        pruned = 0
        if len(self.episodes) > self.max_raw_episodes:
            keep_recent = max(80, self.max_raw_episodes // 2)
            older = self.episodes[:-keep_recent]
            recent = self.episodes[-keep_recent:]
            retained_older: List[Dict[str, Any]] = []
            for ep in older:
                if ep.get("consolidated") and ep.get("feedback") != "negative":
                    self.index.remove(ep["id"])
                    pruned += 1
                else:
                    retained_older.append(ep)
            self.episodes = retained_older + recent

        self.last_consolidation_at = now
        return {
            "schemas_created": created,
            "schemas_updated": updated,
            "pruned": pruned,
            "total_schemas": len(self.schemas),
            "remaining_episodes": len(self.episodes),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episodes": self.episodes[-self.max_raw_episodes:],
            "schemas": self.schemas,
            "last_consolidation_at": self.last_consolidation_at,
            "total_consolidated_episodes": self.total_consolidated_episodes,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "EpisodicMemory":
        em = cls()
        if not isinstance(data, dict):
            return em
        em.last_consolidation_at = float(data.get("last_consolidation_at", 0.0))
        em.total_consolidated_episodes = int(data.get("total_consolidated_episodes", 0))
        schemas = data.get("schemas", {})
        if isinstance(schemas, dict):
            em.schemas = schemas
        episodes = data.get("episodes", [])
        if isinstance(episodes, list):
            for ep in episodes[-em.max_raw_episodes:]:
                if isinstance(ep, dict) and ep.get("id"):
                    em.episodes.append(ep)
                    em._index_episode(ep)
        return em
