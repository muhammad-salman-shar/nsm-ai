"""Typed Role-Filler Hypergraph with Sense Disambiguation, Bayesian Confidence,
Homeostatic Weight Normalization, and Proof-Tracked Defeasible Reasoning."""

import hashlib
import math
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from src.vector_index import FastVectorIndex, STOP_WORDS

_TOKEN_RE = re.compile(r"[a-z0-9_']+")

# Common domain hints for automatic sense disambiguation (polysemy defense)
_SENSE_DOMAINS: Dict[str, Set[str]] = {
    "finance": {"money", "cash", "loan", "account", "rupee", "dollar", "atm", "deposit", "credit", "payment", "raast"},
    "nature": {"river", "water", "shore", "tree", "fish", "forest", "mountain", "rain", "ocean", "animal", "bird"},
    "tech": {"code", "python", "app", "api", "server", "bug", "crash", "script", "cpu", "android", "apk", "ai", "model", "memory", "database"},
    "person": {"man", "woman", "boy", "girl", "friend", "teacher", "founder", "creator", "developer", "brother", "sister", "father"},
}


def normalize_entity(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    cleaned = cleaned.strip(" .,!?;:\"'`()[]{}")
    return cleaned


def tokenize_content(text: str) -> List[str]:
    tokens = _TOKEN_RE.findall((text or "").lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def make_frame_id(
    relation: str,
    agent: str,
    action: str,
    patient: str,
    polarity: int,
) -> str:
    sig = f"{relation}|{agent}|{action}|{patient}|{polarity}"
    return "fr_" + hashlib.blake2b(sig.encode("utf-8"), digest_size=6).hexdigest()


class TypedHypergraph:
    """Role-bound neuro-symbolic knowledge graph with surgical Bayesian updates."""

    def __init__(self, max_hot_frames: int = 5000):
        self.senses: Dict[str, Dict[str, Any]] = {}
        self.frames: Dict[str, Dict[str, Any]] = {}
        self.index = FastVectorIndex(dim=256, max_hot_items=max_hot_frames)
        # Fast adjacency maps (rebuilt in RAM, never serialized redundantly)
        self._by_agent: Dict[str, Set[str]] = {}
        self._by_patient: Dict[str, Set[str]] = {}
        self._by_relation: Dict[str, Set[str]] = {}

    def _index_frame_in_ram(self, frame: Dict[str, Any]) -> None:
        fid = frame["id"]
        agent = frame.get("agent", "")
        patient = frame.get("patient", "")
        rel = frame.get("relation", "")
        action = frame.get("action", "")
        mod = frame.get("modifier", "")

        if agent:
            self._by_agent.setdefault(agent, set()).add(fid)
        if patient:
            self._by_patient.setdefault(patient, set()).add(fid)
        if rel:
            self._by_relation.setdefault(rel, set()).add(fid)

        search_blob = " ".join(
            part for part in [
                agent,
                rel.replace("_", " ").lower(),
                action,
                patient,
                mod,
                frame.get("raw_text", ""),
            ]
            if part
        )
        self.index.add(fid, search_blob)

    def _unindex_frame_in_ram(self, frame: Dict[str, Any]) -> None:
        fid = frame["id"]
        for bucket, key in (
            (self._by_agent, frame.get("agent", "")),
            (self._by_patient, frame.get("patient", "")),
            (self._by_relation, frame.get("relation", "")),
        ):
            if key and key in bucket:
                bucket[key].discard(fid)
                if not bucket[key]:
                    del bucket[key]
        self.index.remove(fid)

    def resolve_sense(self, term: str, context_text: str = "") -> str:
        """Assign or retrieve a context-scoped sense ID to prevent polysemy hairballs."""
        base = normalize_entity(term)
        if not base or base in STOP_WORDS:
            return base

        ctx_tokens = set(tokenize_content(context_text))
        detected_domain = "general"
        best_overlap = 0
        for domain, keywords in _SENSE_DOMAINS.items():
            overlap = len(ctx_tokens.intersection(keywords))
            if overlap > best_overlap:
                best_overlap = overlap
                detected_domain = domain

        # If term already exists under a specific domain and no new domain is detected, reuse it
        existing_for_base = [
            sid for sid, sdata in self.senses.items() if sdata.get("lemma") == base
        ]
        if detected_domain == "general" and len(existing_for_base) == 1:
            sense_id = existing_for_base[0]
        else:
            sense_id = f"{base}#{detected_domain}"

        now = time.time()
        if sense_id not in self.senses:
            self.senses[sense_id] = {
                "lemma": base,
                "domain": detected_domain,
                "context_tokens": sorted(ctx_tokens)[:30],
                "hits": 1,
                "updated_at": now,
            }
        else:
            entry = self.senses[sense_id]
            merged_ctx = set(entry.get("context_tokens", []))
            merged_ctx.update(ctx_tokens)
            entry["context_tokens"] = sorted(merged_ctx)[:40]
            entry["hits"] = int(entry.get("hits", 0)) + 1
            entry["updated_at"] = now

        return sense_id

    @staticmethod
    def bayesian_confidence(frame: Dict[str, Any]) -> float:
        alpha = max(0.1, float(frame.get("alpha", 1.5)))
        beta = max(0.1, float(frame.get("beta", 0.5)))
        return round(alpha / (alpha + beta), 4)

    def normalize_outgoing_weights(self, agent: str) -> None:
        """Homeostatic normalization: outgoing weights from any entity sum to 1.0."""
        fids = self._by_agent.get(agent)
        if not fids:
            return
        now = time.time()
        raw_scores: List[Tuple[str, float]] = []
        total = 0.0
        for fid in fids:
            fr = self.frames.get(fid)
            if not fr:
                continue
            conf = self.bayesian_confidence(fr)
            age_days = max(0.0, (now - float(fr.get("updated_at", now))) / 86400.0)
            # Gentle recency decay (core built-in facts never decay below 0.9)
            decay = 1.0 if fr.get("source") == "core" else math.exp(-0.008 * age_days)
            score = max(0.02, conf * decay)
            raw_scores.append((fid, score))
            total += score

        if total <= 1e-8:
            return
        for fid, score in raw_scores:
            self.frames[fid]["norm_weight"] = round(score / total, 4)

    def add_frame(
        self,
        relation: str,
        agent: str,
        patient: str,
        action: str = "",
        modifier: str = "",
        polarity: int = 1,
        source: str = "user",
        raw_text: str = "",
        confidence_boost: float = 1.0,
    ) -> Dict[str, Any]:
        """Insert or reinforce a role-bound hypergraph frame."""
        norm_agent = normalize_entity(agent)
        norm_patient = normalize_entity(patient)
        norm_action = normalize_entity(action)
        norm_rel = (relation or "RELATED_TO").strip().upper()
        pol = -1 if polarity < 0 else 1

        if not norm_agent or not norm_patient:
            raise ValueError("Both agent and patient are required for a hypergraph frame.")

        # Reject trivial circular definitions (e.g., "dog IS_A dog")
        if norm_rel in {"IS_A", "DEFINED_AS", "EQUALS"} and norm_agent == norm_patient:
            raise ValueError("Circular definition rejected.")

        ctx = raw_text or f"{norm_agent} {norm_action} {norm_patient}"
        agent_sense = self.resolve_sense(norm_agent, ctx)
        patient_sense = self.resolve_sense(norm_patient, ctx)

        fid = make_frame_id(norm_rel, norm_agent, norm_action, norm_patient, pol)
        now = time.time()

        if fid in self.frames:
            fr = self.frames[fid]
            fr["alpha"] = round(float(fr.get("alpha", 1.5)) + max(0.25, confidence_boost), 3)
            fr["evidence_count"] = int(fr.get("evidence_count", 1)) + 1
            fr["updated_at"] = now
            if raw_text:
                fr["raw_text"] = raw_text[:280]
            if modifier and not fr.get("modifier"):
                fr["modifier"] = modifier[:120]
        else:
            init_alpha = 4.0 if source == "core" else (1.5 + max(0.0, confidence_boost))
            fr = {
                "id": fid,
                "relation": norm_rel,
                "agent": norm_agent,
                "agent_sense": agent_sense,
                "action": norm_action,
                "patient": norm_patient,
                "patient_sense": patient_sense,
                "modifier": (modifier or "")[:120],
                "polarity": pol,
                "alpha": round(init_alpha, 3),
                "beta": 0.5,
                "norm_weight": 1.0,
                "evidence_count": 1,
                "source": source,
                "raw_text": (raw_text or "")[:280],
                "created_at": now,
                "updated_at": now,
            }
            self.frames[fid] = fr

        self._index_frame_in_ram(fr)
        self.normalize_outgoing_weights(norm_agent)
        return fr

    def surgical_update(
        self,
        frame_ids: List[str],
        reward: float,
        only_last_culprit: bool = False,
    ) -> List[Dict[str, Any]]:
        """Surgical Credit Assignment: update Bayesian confidence ONLY on exact traced frames."""
        if not frame_ids:
            return []
        targets = [frame_ids[-1]] if (only_last_culprit and len(frame_ids) > 1) else list(frame_ids)
        updated: List[Dict[str, Any]] = []
        affected_agents: Set[str] = set()

        for fid in targets:
            fr = self.frames.get(fid)
            if not fr:
                continue
            # Protect immutable core identity frames from accidental erasure
            if fr.get("source") == "core" and reward < 0:
                continue
            if reward >= 0:
                fr["alpha"] = round(float(fr.get("alpha", 1.5)) + abs(reward), 3)
            else:
                fr["beta"] = round(float(fr.get("beta", 0.5)) + abs(reward), 3)
            fr["updated_at"] = time.time()
            affected_agents.add(fr.get("agent", ""))
            updated.append({
                "frame_id": fid,
                "new_confidence": self.bayesian_confidence(fr),
            })

        for ag in affected_agents:
            if ag:
                self.normalize_outgoing_weights(ag)
        return updated

    def remove_entity(self, entity: str) -> int:
        target = normalize_entity(entity)
        if not target:
            return 0
        to_remove = [
            fid
            for fid, fr in self.frames.items()
            if fr.get("source") != "core"
            and (fr.get("agent") == target or fr.get("patient") == target)
        ]
        for fid in to_remove:
            fr = self.frames.pop(fid, None)
            if fr:
                self._unindex_frame_in_ram(fr)
        return len(to_remove)

    def get_frames_for_agent(
        self,
        agent: str,
        relation: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        key = normalize_entity(agent)
        fids = self._by_agent.get(key, set())
        out = []
        for fid in fids:
            fr = self.frames.get(fid)
            if not fr:
                continue
            if relation and fr.get("relation") != relation.upper():
                continue
            out.append(fr)
        out.sort(key=lambda x: (self.bayesian_confidence(x), x.get("updated_at", 0.0)), reverse=True)
        return out

    def get_frames_for_patient(
        self,
        patient: str,
        relation: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        key = normalize_entity(patient)
        fids = self._by_patient.get(key, set())
        out = []
        for fid in fids:
            fr = self.frames.get(fid)
            if not fr:
                continue
            if relation and fr.get("relation") != relation.upper():
                continue
            out.append(fr)
        out.sort(key=lambda x: (self.bayesian_confidence(x), x.get("updated_at", 0.0)), reverse=True)
        return out

    def query_capability_or_relation(
        self,
        subject: str,
        relation: str,
        target: Optional[str] = None,
        max_hops: int = 4,
    ) -> Dict[str, Any]:
        """Proof-tracked defeasible reasoning across direct frames and IS_A chains."""
        subj = normalize_entity(subject)
        rel = relation.upper()
        tgt = normalize_entity(target) if target else ""

        # 1. Direct stored frames (check both positive and negative polarity for contradiction/defeasibility)
        direct = self.get_frames_for_agent(subj, relation=rel)
        if tgt:
            direct = [f for f in direct if f.get("patient") == tgt or tgt in f.get("patient", "")]

        pos_direct = [f for f in direct if f.get("polarity", 1) > 0 and self.bayesian_confidence(f) >= 0.35]
        neg_direct = [f for f in direct if f.get("polarity", 1) < 0 and self.bayesian_confidence(f) >= 0.35]

        if pos_direct and neg_direct:
            best_pos = pos_direct[0]
            best_neg = neg_direct[0]
            return {
                "mode": "contradicted",
                "frames": [best_pos, best_neg],
                "used_frame_ids": [best_pos["id"], best_neg["id"]],
                "confidence": round(max(self.bayesian_confidence(best_pos), self.bayesian_confidence(best_neg)), 3),
                "proof_steps": [
                    f"Stored claim (+): {best_pos['agent']} {rel} {best_pos['patient']} (conf={self.bayesian_confidence(best_pos)})",
                    f"Stored counter-claim (-): {best_neg['agent']} NOT {rel} {best_neg['patient']} (conf={self.bayesian_confidence(best_neg)})",
                ],
            }

        if neg_direct:
            best = neg_direct[0]
            return {
                "mode": "stored",
                "polarity": -1,
                "frames": [best],
                "used_frame_ids": [best["id"]],
                "confidence": self.bayesian_confidence(best),
                "proof_steps": [
                    f"Direct exception: {best['agent']} NOT {rel} {best['patient']} (conf={self.bayesian_confidence(best)})"
                ],
            }

        if pos_direct:
            best = pos_direct[0]
            return {
                "mode": "stored",
                "polarity": 1,
                "frames": pos_direct[:5],
                "used_frame_ids": [f["id"] for f in pos_direct[:5]],
                "confidence": self.bayesian_confidence(best),
                "proof_steps": [
                    f"Direct fact: {best['agent']} {rel} {best['patient']} (conf={self.bayesian_confidence(best)})"
                ],
            }

        # 2. Multi-hop IS_A inheritance (Defeasible BFS)
        visited: Set[str] = {subj}
        queue: List[Tuple[str, List[str], List[str], float]] = [(subj, [], [], 1.0)]

        while queue:
            curr, path_steps, path_fids, path_conf = queue.pop(0)
            if len(path_fids) >= max_hops:
                continue

            isa_frames = [
                f for f in self.get_frames_for_agent(curr, relation="IS_A")
                if f.get("polarity", 1) > 0 and self.bayesian_confidence(f) >= 0.4
            ]
            for isa in isa_frames:
                parent = isa["patient"]
                if parent in visited:
                    continue
                visited.add(parent)
                step_conf = round(path_conf * self.bayesian_confidence(isa), 4)
                step_txt = f"{curr} IS_A {parent} (conf={self.bayesian_confidence(isa)})"
                next_steps = path_steps + [step_txt]
                next_fids = path_fids + [isa["id"]]

                # Check if parent has the target relation
                parent_rel = self.get_frames_for_agent(parent, relation=rel)
                if tgt:
                    parent_rel = [f for f in parent_rel if f.get("patient") == tgt or tgt in f.get("patient", "")]
                valid_parent = [f for f in parent_rel if self.bayesian_confidence(f) >= 0.4]
                if valid_parent:
                    top_p = valid_parent[0]
                    pol = top_p.get("polarity", 1)
                    final_conf = round(step_conf * self.bayesian_confidence(top_p), 4)
                    sign = "" if pol > 0 else "NOT "
                    return {
                        "mode": "derived",
                        "polarity": pol,
                        "frames": [top_p],
                        "used_frame_ids": next_fids + [top_p["id"]],
                        "confidence": final_conf,
                        "proof_steps": next_steps + [
                            f"Inherited: {parent} {sign}{rel} {top_p['patient']} (conf={self.bayesian_confidence(top_p)})"
                        ],
                    }

                queue.append((parent, next_steps, next_fids, step_conf))

        return {
            "mode": "unknown",
            "polarity": 0,
            "frames": [],
            "used_frame_ids": [],
            "confidence": 0.0,
            "proof_steps": [],
        }

    def semantic_search(self, query: str, top_k: int = 6, min_score: float = 0.2) -> List[Tuple[Dict[str, Any], float]]:
        hits = self.index.search(query, top_k=top_k, min_score=min_score)
        results: List[Tuple[Dict[str, Any], float]] = []
        for fid, sim in hits:
            fr = self.frames.get(fid)
            if fr:
                combined = round(sim * (0.5 + 0.5 * self.bayesian_confidence(fr)), 4)
                results.append((fr, combined))
        results.sort(key=lambda item: item[1], reverse=True)
        return results

    def sentence_token_match(
        self,
        sentence: str,
        min_ref_pct: float = 0.20,
        direct_lift_pct: float = 0.40,
    ) -> Dict[str, Any]:
        """Treat a full sentence as a token unit and score word-level overlap against stored memory sentences.

        Rules:
        - match_pct >= 0.40 (40%+): Direct sentence lift ('direct_lift', mode='stored')
        - 0.20 <= match_pct < 0.40 (20%-39%): Reference match ('reference_match', mode='derived')
        - match_pct < 0.20: Unknown ('none', mode='unknown')
        """
        from src import realizer as _realizer

        raw = (sentence or "").strip()
        if not raw:
            return {"mode": "unknown", "tier": "none", "match_pct": 0.0, "frames": [], "used_frame_ids": [], "confidence": 0.0, "proof_steps": []}

        # Extract meaningful word tokens from the input sentence
        q_words = set(tokenize_content(raw))
        # Preserve important 2-letter technical/domain words while ignoring glue stopwords
        glue = {
            "is", "am", "are", "was", "were", "be", "to", "of", "in", "on", "at", "by",
            "an", "as", "or", "if", "it", "my", "me", "we", "us", "he", "she", "do", "so",
            "no", "up", "go", "ok", "hi",
        }
        for tok in re.findall(r"[a-z0-9]+", raw.lower()):
            if len(tok) == 2 and tok not in glue:
                q_words.add(tok)

        if not q_words:
            q_words = {tok for tok in re.findall(r"[a-z0-9]+", raw.lower()) if len(tok) >= 2}
        if not q_words:
            return {"mode": "unknown", "tier": "none", "match_pct": 0.0, "frames": [], "used_frame_ids": [], "confidence": 0.0, "proof_steps": []}

        scored: List[Tuple[float, float, Dict[str, Any], str]] = []
        for fr in self.frames.values():
            ag = (fr.get("agent") or "").strip()
            if not ag:
                continue
            mem_sent = _realizer.frame_to_sentence(fr)
            mem_blob = f"{ag} {fr.get('patient', '')} {mem_sent}"
            m_words = set(tokenize_content(mem_blob))
            for tok in re.findall(r"[a-z0-9]+", mem_blob.lower()):
                if len(tok) == 2 and tok not in glue:
                    m_words.add(tok)
            if not m_words:
                continue

            matched = q_words.intersection(m_words)
            if not matched:
                continue

            input_pct = len(matched) / len(q_words)
            mem_pct = len(matched) / len(m_words)
            # Bidirectional coverage when 2+ words match so long queries against concise memories still lift cleanly
            eff_pct = max(input_pct, 0.85 * mem_pct) if len(matched) >= 2 else input_pct
            eff_pct = min(1.0, round(eff_pct, 4))

            if eff_pct >= min_ref_pct:
                b_conf = self.bayesian_confidence(fr)
                rank_score = eff_pct + (0.10 * mem_pct) + (0.05 * b_conf)
                scored.append((rank_score, eff_pct, fr, mem_sent))

        if not scored:
            return {
                "mode": "unknown",
                "tier": "none",
                "match_pct": 0.0,
                "frames": [],
                "used_frame_ids": [],
                "confidence": 0.0,
                "proof_steps": [f"Sentence-token scan: 0% >= 20% threshold for '{raw[:60]}'."],
            }

        scored.sort(key=lambda item: item[0], reverse=True)
        _, best_pct, best_fr, best_sent = scored[0]
        pct_label = round(best_pct * 100, 1)

        if best_pct >= direct_lift_pct:
            conf = round(min(0.98, 0.65 + 0.33 * best_pct), 3)
            return {
                "mode": "stored",
                "tier": "direct_lift",
                "match_pct": best_pct,
                "frames": [best_fr],
                "used_frame_ids": [best_fr["id"]],
                "confidence": conf,
                "sentence": best_sent,
                "proof_steps": [
                    f"Sentence-token direct lift ({pct_label}% >= 40%): '{best_sent}'"
                ],
            }

        # 20% to 39%: answer from the highest-scoring memory reference(s)
        chosen_frames = [best_fr]
        chosen_ids = [best_fr["id"]]
        proofs = [f"Sentence-token reference match ({pct_label}% >= 20%): '{best_sent}'"]
        if len(scored) > 1 and scored[1][1] >= min_ref_pct and scored[1][2]["id"] != best_fr["id"]:
            sec_pct, sec_fr, sec_sent = scored[1][1], scored[1][2], scored[1][3]
            if sec_sent != best_sent:
                chosen_frames.append(sec_fr)
                chosen_ids.append(sec_fr["id"])
                proofs.append(f"Secondary memory reference ({round(sec_pct * 100, 1)}%): '{sec_sent}'")

        conf = round(min(0.79, 0.45 + 0.70 * best_pct), 3)
        return {
            "mode": "derived",
            "tier": "reference_match",
            "match_pct": best_pct,
            "frames": chosen_frames,
            "used_frame_ids": chosen_ids,
            "confidence": conf,
            "sentence": _realizer.realize_frames(chosen_frames, max_items=2),
            "proof_steps": proofs,
        }

    def resolve_alias(self, term: str) -> str:
        """Resolve an entity name or alias (ALSO_KNOWN_AS) to its primary graph node."""
        norm = normalize_entity(term)
        if not norm:
            return norm
        if norm in self._by_agent:
            # If node only exists as an alias pointing to a richer node, follow it
            aka_out = self.get_frames_for_agent(norm, relation="ALSO_KNOWN_AS")
            if aka_out and len(self._by_agent.get(norm, set())) == len(aka_out):
                target = aka_out[0].get("patient", "")
                if target and target in self._by_agent:
                    return target
            return norm
        # Reverse alias check: user asked about the alias stored in patient
        aka_in = self.get_frames_for_patient(norm, relation="ALSO_KNOWN_AS")
        if aka_in:
            return aka_in[0].get("agent", norm)
        return norm

    def get_frames_by_relation(self, relation: str) -> List[Dict[str, Any]]:
        rel = (relation or "").strip().upper()
        fids = self._by_relation.get(rel, set())
        frames = [self.frames[fid] for fid in fids if fid in self.frames]
        frames.sort(key=lambda x: (self.bayesian_confidence(x), x.get("updated_at", 0.0)), reverse=True)
        return frames

    def query_examples(self, category: str, limit: int = 6) -> Dict[str, Any]:
        """Find concrete instances/examples of a category via reverse IS_A and HAS_BRANCHES."""
        cat = self.resolve_alias(category)
        # Handle simple plural category names (e.g. "data structures" -> "data structure")
        candidates = [cat]
        if cat.endswith("s") and len(cat) > 3:
            candidates.append(cat[:-1])

        matched_frames: List[Dict[str, Any]] = []
        examples: List[str] = []
        seen_ex: Set[str] = set()

        for c in candidates:
            rev_isa = self.get_frames_for_patient(c, relation="IS_A")
            for fr in rev_isa:
                if fr.get("polarity", 1) > 0 and self.bayesian_confidence(fr) >= 0.35:
                    ag = fr.get("agent", "")
                    if ag and ag not in seen_ex:
                        seen_ex.add(ag)
                        examples.append(ag)
                        matched_frames.append(fr)
            br_frames = self.get_frames_for_agent(c, relation="HAS_BRANCHES")
            for fr in br_frames:
                if self.bayesian_confidence(fr) >= 0.35 and fr not in matched_frames:
                    matched_frames.append(fr)

        if matched_frames:
            top_frames = matched_frames[:limit]
            avg_conf = sum(self.bayesian_confidence(f) for f in top_frames) / len(top_frames)
            proofs = [
                f"Instance lookup: {f['agent']} {f['relation']} {f['patient']} (conf={self.bayesian_confidence(f)})"
                for f in top_frames
            ]
            return {
                "mode": "stored",
                "examples": examples[:limit],
                "frames": top_frames,
                "used_frame_ids": [f["id"] for f in top_frames],
                "confidence": round(avg_conf, 3),
                "proof_steps": proofs,
            }

        return {
            "mode": "unknown",
            "examples": [],
            "frames": [],
            "used_frame_ids": [],
            "confidence": 0.0,
            "proof_steps": [f"No IS_A instances or branches found for '{cat}'."],
        }

    def query_causal(self, effect: str) -> Dict[str, Any]:
        """Find what causes an effect via CAUSES (reverse) and IF_THEN (reverse)."""
        eff = self.resolve_alias(effect)
        eff_tokens = set(tokenize_content(eff))
        matches: List[Tuple[Dict[str, Any], float]] = []

        for rel in ("CAUSES", "IF_THEN"):
            for fr in self.get_frames_by_relation(rel):
                if self.bayesian_confidence(fr) < 0.35:
                    continue
                pat = fr.get("patient", "")
                ag = fr.get("agent", "")
                if eff == pat or (eff and eff in pat):
                    matches.append((fr, 1.0))
                elif eff == ag or (eff and eff in ag):
                    matches.append((fr, 0.85))
                elif eff_tokens:
                    pat_toks = set(tokenize_content(pat))
                    overlap = len(eff_tokens.intersection(pat_toks))
                    if overlap >= max(1, len(eff_tokens) // 2 + 1) or (len(eff_tokens) == 1 and overlap == 1):
                        matches.append((fr, overlap / max(1, len(eff_tokens))))

        matches.sort(key=lambda x: (x[1], self.bayesian_confidence(x[0])), reverse=True)
        if matches:
            top = [f for f, _ in matches[:3]]
            conf = round(self.bayesian_confidence(top[0]), 3)
            proofs = [
                f"Causal trace: {f['agent']} {f['relation']} {f['patient']} (conf={self.bayesian_confidence(f)})"
                for f in top
            ]
            return {
                "mode": "stored",
                "frames": top,
                "used_frame_ids": [f["id"] for f in top],
                "confidence": conf,
                "proof_steps": proofs,
            }
        return {
            "mode": "unknown",
            "frames": [],
            "used_frame_ids": [],
            "confidence": 0.0,
            "proof_steps": [f"No causal rule found for '{eff}'."],
        }

    def query_consequence(self, condition: str) -> Dict[str, Any]:
        """Find what happens if a condition occurs via IF_THEN and forward CAUSES."""
        cond = normalize_entity(condition)
        cond_tokens = set(tokenize_content(cond))
        matches: List[Tuple[Dict[str, Any], float]] = []

        for rel in ("IF_THEN", "CAUSES"):
            for fr in self.get_frames_by_relation(rel):
                if self.bayesian_confidence(fr) < 0.35:
                    continue
                ag = fr.get("agent", "")
                if cond == ag or (cond and (cond in ag or ag in cond)):
                    matches.append((fr, 1.0))
                elif cond_tokens:
                    ag_toks = set(tokenize_content(ag))
                    overlap = len(cond_tokens.intersection(ag_toks))
                    if overlap >= 2 or (len(cond_tokens) == 1 and overlap == 1):
                        score = overlap / max(1, len(cond_tokens.union(ag_toks)))
                        matches.append((fr, score))

        matches.sort(key=lambda x: (x[1], self.bayesian_confidence(x[0])), reverse=True)
        if matches:
            top = [f for f, _ in matches[:3]]
            conf = round(self.bayesian_confidence(top[0]), 3)
            proofs = [
                f"Consequence rule: IF {f['agent']} -> {f['patient']} (conf={self.bayesian_confidence(f)})"
                for f in top
            ]
            return {
                "mode": "stored",
                "frames": top,
                "used_frame_ids": [f["id"] for f in top],
                "confidence": conf,
                "proof_steps": proofs,
            }
        return {
            "mode": "unknown",
            "frames": [],
            "used_frame_ids": [],
            "confidence": 0.0,
            "proof_steps": [f"No IF_THEN or causal consequence stored for '{cond}'."],
        }

    def query_verify(self, subject: str, relation: str, target: str) -> Dict[str, Any]:
        """Polar Yes/No verification with inheritance, definition check, and strict unknown boundary."""
        subj = self.resolve_alias(subject)
        tgt = normalize_entity(target)
        rel = (relation or "IS_A").upper()

        # 1. Direct & inherited relation check
        res = self.query_capability_or_relation(subj, rel, tgt)
        if res["mode"] in {"stored", "derived", "contradicted"}:
            return res

        # 2. Check cross-relations for IS_A / DEFINED_AS / HAS_PART / HAS
        alt_rels = ["DEFINED_AS", "IS_A", "HAS", "HAS_PART", "ALSO_KNOWN_AS"]
        tgt_tokens = set(tokenize_content(tgt))
        for alt in alt_rels:
            for fr in self.get_frames_for_agent(subj, relation=alt):
                if self.bayesian_confidence(fr) < 0.35:
                    continue
                pat = fr.get("patient", "")
                if tgt == pat or (len(tgt) >= 3 and re.search(r"\b" + re.escape(tgt) + r"\b", pat)):
                    return {
                        "mode": "stored",
                        "polarity": fr.get("polarity", 1),
                        "frames": [fr],
                        "used_frame_ids": [fr["id"]],
                        "confidence": self.bayesian_confidence(fr),
                        "proof_steps": [
                            f"Verified via {alt}: {fr['agent']} {alt} {fr['patient']} (conf={self.bayesian_confidence(fr)})"
                        ],
                    }
                if tgt_tokens and len(tgt_tokens) >= 2:
                    pat_tokens = set(tokenize_content(pat))
                    if tgt_tokens.issubset(pat_tokens):
                        return {
                            "mode": "stored",
                            "polarity": fr.get("polarity", 1),
                            "frames": [fr],
                            "used_frame_ids": [fr["id"]],
                            "confidence": self.bayesian_confidence(fr),
                            "proof_steps": [
                                f"Verified via {alt} tokens: {fr['agent']} {alt} {fr['patient']}"
                            ],
                        }

        # 3. Unknown (attach known frames about subject so realizer can give a helpful honest reply)
        known = self.get_frames_for_agent(subj)[:2]
        return {
            "mode": "unknown",
            "polarity": 0,
            "frames": known,
            "used_frame_ids": [f["id"] for f in known],
            "confidence": 0.0,
            "proof_steps": [f"No direct or inherited link confirms '{subj} {rel} {tgt}'."],
        }

    def compare_entities(self, entity_a: str, entity_b: str) -> Dict[str, Any]:
        """Compare two entities using explicit COMPARED_TO links plus side-by-side hypergraph profiles."""
        a = self.resolve_alias(entity_a)
        b = self.resolve_alias(entity_b)

        direct_comp: List[Dict[str, Any]] = []
        for fr in self.get_frames_by_relation("COMPARED_TO"):
            ag, pat = fr.get("agent", ""), fr.get("patient", "")
            if (ag == a and pat == b) or (ag == b and pat == a):
                direct_comp.append(fr)

        direct_ids = {f["id"] for f in direct_comp}
        frames_a = [f for f in self.get_frames_for_agent(a) if f["id"] not in direct_ids][:3]
        frames_b = [f for f in self.get_frames_for_agent(b) if f["id"] not in direct_ids][:3]

        if not direct_comp and not frames_a and not frames_b:
            return {
                "mode": "unknown",
                "entity_a": a,
                "entity_b": b,
                "direct_comparisons": [],
                "frames_a": [],
                "frames_b": [],
                "shared_categories": [],
                "used_frame_ids": [],
                "confidence": 0.0,
                "proof_steps": [f"No stored facts found for '{a}' or '{b}' to compare."],
            }

        cats_a = {f["patient"] for f in self.get_frames_for_agent(a, relation="IS_A") if f.get("polarity", 1) > 0}
        cats_b = {f["patient"] for f in self.get_frames_for_agent(b, relation="IS_A") if f.get("polarity", 1) > 0}
        shared = sorted(cats_a.intersection(cats_b))

        used_frames = direct_comp + frames_a + frames_b
        used_ids = list(dict.fromkeys(f["id"] for f in used_frames))
        avg_conf = sum(self.bayesian_confidence(f) for f in used_frames) / max(1, len(used_frames))
        proofs = [
            f"Compare node: {f['agent']} {f['relation']} {f['patient']} (conf={self.bayesian_confidence(f)})"
            for f in used_frames[:6]
        ]

        mode = "stored" if (direct_comp or (frames_a and frames_b)) else "derived"
        return {
            "mode": mode,
            "entity_a": a,
            "entity_b": b,
            "direct_comparisons": direct_comp,
            "frames_a": frames_a,
            "frames_b": frames_b,
            "shared_categories": shared,
            "used_frame_ids": used_ids,
            "confidence": round(avg_conf, 3),
            "proof_steps": proofs,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "senses": self.senses,
            "frames": self.frames,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "TypedHypergraph":
        hg = cls()
        if not isinstance(data, dict):
            return hg
        senses = data.get("senses", {})
        if isinstance(senses, dict):
            hg.senses = senses
        frames = data.get("frames", {})
        if isinstance(frames, dict):
            for fid, fr in frames.items():
                if isinstance(fr, dict) and fr.get("agent") and fr.get("patient"):
                    fr.setdefault("id", fid)
                    hg.frames[fr["id"]] = fr
                    hg._index_frame_in_ram(fr)
        return hg
