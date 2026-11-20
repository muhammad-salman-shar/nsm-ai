"""NSM VB v1.4 - NeuraSaMu Neuro-Symbolic Cognitive Brain.

Core Architecture:
1. Typed Role-Filler Hypergraph (binding-safe, sense-disambiguated, Bayesian confidence).
2. Two-Tier Fast RAM Vector Index + Cold SQLite Persistence.
3. Proof-Tracked Defeasible Reasoning + Surgical Credit Assignment.
4. Episodic Recall Trace + Offline Sleep Consolidation Engine.
5. Optional Samu Lab / OpenAI-Compatible API Language Cortex.
"""

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from src import cortex_api
from src.episodic import EpisodicMemory
from src.hypergraph import TypedHypergraph, normalize_entity

# Irregular verb normalization map for clean role-bound SVO matching
_VERB_LEMMA = {
    "bit": "bite", "bites": "bite", "bitten": "bite",
    "ate": "eat", "eats": "eat", "eaten": "eat",
    "chased": "chase", "chases": "chase",
    "built": "build", "builds": "build",
    "created": "create", "creates": "create",
    "made": "make", "makes": "make",
    "wrote": "write", "writes": "write", "written": "write",
    "killed": "kill", "kills": "kill",
    "helped": "help", "helps": "help",
    "loved": "love", "loves": "love",
    "hated": "hate", "hates": "hate",
    "liked": "like", "likes": "like",
    "saw": "see", "sees": "see", "seen": "see",
    "hit": "hit", "hits": "hit",
    "taught": "teach", "teaches": "teach",
    "broke": "break", "breaks": "break", "broken": "break",
    "fixed": "fix", "fixes": "fix",
}

_GREETINGS = frozenset({
    "hi", "hello", "hey", "yo", "hola", "salam", "assalam", "assalamualaikum",
    "good morning", "good evening", "good afternoon", "gm", "sup",
})

_NEG_FEEDBACK_PHRASES = (
    "that's wrong", "that is wrong", "you are wrong", "wrong answer",
    "incorrect", "galat", "nope wrong", "no that's wrong", "not right",
    "bad answer", "false",
)

_POS_FEEDBACK_PHRASES = (
    "good job", "correct", "that's right", "that is right", "exact",
    "spot on", "sahi", "well done", "nice answer", "perfect",
)

_SELF_TRIGGERS = (
    "who are you", "what are you", "your name", "who made you",
    "who created you", "who built you", "about yourself", "tell me about you",
    "what is nsm", "who is your creator", "who is your founder",
    "what is neurasamu", "tell me about neurasamu",
)


def _canon_verb(verb: str) -> str:
    v = normalize_entity(verb)
    if v in _VERB_LEMMA:
        return _VERB_LEMMA[v]
    if len(v) > 4 and v.endswith("ed"):
        return v[:-2]
    if len(v) > 3 and v.endswith("s") and not v.endswith("ss"):
        return v[:-1]
    return v


def _clean_phrase(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    s = s.strip(" .,!?;:\"'`")
    # Strip leading articles for clean canonical entities
    s = re.sub(r"^(?:a|an|the)\s+", "", s, flags=re.IGNORECASE)
    return s.strip()


_ACRONYM_MAP = {
    "cpu": "CPU",
    "ram": "RAM",
    "gpu": "GPU",
    "api": "API",
    "sql": "SQL",
    "sqlite": "SQLite",
    "ai": "AI",
    "os": "OS",
    "nsm": "NSM",
    "nsm vb": "NSM VB",
    "neurasamu": "NeuraSaMu",
    "big o notation": "Big O notation",
}


def _display_entity(name: str) -> str:
    low = (name or "").strip().lower()
    if low in _ACRONYM_MAP:
        return _ACRONYM_MAP[low]
    words = low.split()
    return " ".join(_ACRONYM_MAP.get(w, w.capitalize()) for w in words)


class Brain:
    """NSM VB v1.4 cognitive engine."""

    VERSION = "1.4"

    def __init__(self, seed_core: bool = True):
        self.version = self.VERSION
        self.hypergraph = TypedHypergraph(max_hot_frames=5000)
        self.episodic = EpisodicMemory(max_raw_episodes=180)
        self.profile: Dict[str, str] = {}
        self.created_at: float = time.time()
        self.updated_at: float = self.created_at
        self.turn_count: int = 0
        if seed_core:
            self._seed_core_knowledge()

    def _seed_core_knowledge(self) -> None:
        """Seed immutable core NeuraSaMu & NSM VB v1.4 identity knowledge."""
        core_facts = [
            ("IS_A", "nsm vb", "neuro-symbolic virtual brain", "", 1, "NSM VB is a neuro-symbolic virtual brain built by NeuraSaMu."),
            ("DEFINED_AS", "nsm vb", "version 1.4 cognitive architecture with typed hypergraph memory, episodic recall trace, surgical credit assignment, and sleep consolidation", "", 1, "NSM VB v1.4 architecture overview."),
            ("CREATED", "muhammad salman shar", "nsm vb", "created", 1, "Muhammad Salman Shar created NSM VB."),
            ("CREATED", "muhammad salman shar", "neurasamu", "founded", 1, "Muhammad Salman Shar founded NeuraSaMu."),
            ("IS_A", "muhammad salman shar", "founder of neurasamu and creator of nsm vb", "", 1, "Muhammad Salman Shar (Salman / Akira) is the founder of NeuraSaMu."),
            ("IS_A", "neurasamu", "independent ai research and software development lab", "", 1, "NeuraSaMu is an independent AI research and software lab at neurasamu.com."),
            ("HAS", "neurasamu", "official website neurasamu.com", "", 1, "NeuraSaMu website is neurasamu.com."),
            ("CAN", "nsm vb", "learn role-bound facts, reason with proof traces, recall past episodes, and consolidate memory offline", "", 1, "NSM VB core capabilities."),
        ]
        for rel, ag, pat, act, pol, raw in core_facts:
            try:
                self.hypergraph.add_frame(
                    relation=rel,
                    agent=ag,
                    patient=pat,
                    action=act,
                    polarity=pol,
                    source="core",
                    raw_text=raw,
                    confidence_boost=1.0,
                )
            except ValueError:
                pass

    def _reply(
        self,
        user_input: str,
        response: str,
        intent: str,
        mode: str,
        confidence: float,
        recalled_ids: Optional[List[str]] = None,
        proof_steps: Optional[List[str]] = None,
        learned: Optional[List[str]] = None,
        cortex_used: bool = False,
        record_episode: bool = True,
    ) -> Dict[str, Any]:
        recalled = recalled_ids or []
        proof = proof_steps or []
        ep = None
        if record_episode:
            ep = self.episodic.record(
                user_input=user_input,
                intent=intent,
                recalled_frame_ids=recalled,
                proof_steps=proof,
                response=response,
                confidence=confidence,
                mode=mode,
            )
        self.turn_count += 1
        self.updated_at = time.time()
        return {
            "response": response,
            "mode": mode,
            "intent": intent,
            "confidence": round(float(confidence), 3),
            "recalled_frame_ids": recalled,
            "proof_steps": proof,
            "learned": learned or [],
            "episode_id": ep["id"] if ep else None,
            "cortex_used": cortex_used,
            "stats": {
                "frames": len(self.hypergraph.frames),
                "senses": len(self.hypergraph.senses),
                "episodes": len(self.episodic.episodes),
                "schemas": len(self.episodic.schemas),
            },
        }

    def apply_feedback(self, positive: bool, episode_id: Optional[str] = None) -> Dict[str, Any]:
        """Surgical Credit Assignment on exact recalled frames of an episode."""
        target_ep = None
        if episode_id:
            for ep in reversed(self.episodic.episodes):
                if ep.get("id") == episode_id:
                    target_ep = ep
                    break
        if target_ep is None:
            target_ep = self.episodic.get_last_episode(skip_meta=True)

        if not target_ep:
            return {"ok": False, "message": "No previous episode found to update.", "updated": []}

        target_ep["feedback"] = "positive" if positive else "negative"
        fids = target_ep.get("recalled_frame_ids", [])
        if not fids:
            return {
                "ok": True,
                "message": "Feedback logged on episode (no symbolic frames needed adjustment).",
                "episode_id": target_ep["id"],
                "updated": [],
            }

        reward = 0.8 if positive else -1.2
        updated = self.hypergraph.surgical_update(
            frame_ids=fids,
            reward=reward,
            only_last_culprit=(not positive),
        )
        self.updated_at = time.time()
        return {
            "ok": True,
            "episode_id": target_ep["id"],
            "feedback": target_ep["feedback"],
            "updated": updated,
            "message": (
                f"Reinforced {len(updated)} exact memory link(s)."
                if positive
                else f"Surgical correction applied to culprit link ({len(updated)} frame adjusted; unrelated knowledge untouched)."
            ),
        }

    def run_sleep_consolidation(self, force: bool = True) -> Dict[str, Any]:
        """Trigger Offline Sleep Consolidation Engine."""
        report = self.episodic.consolidate(force=force)
        # Re-normalize outgoing weights across all active agents during sleep
        for agent in list(self.hypergraph._by_agent.keys()):
            self.hypergraph.normalize_outgoing_weights(agent)
        self.updated_at = time.time()
        return report

    def _handle_meta_recall(self, text: str) -> Optional[Dict[str, Any]]:
        low = text.lower().strip()
        if any(
            k in low
            for k in (
                "what did you recall",
                "what did i ask",
                "last conversation",
                "previous episode",
                "explain your reasoning",
                "show proof",
                "why did you say",
                "last recall",
                "pichli baar",
                "pichla recall",
            )
        ):
            last_ep = self.episodic.get_last_episode(skip_meta=True)
            if not last_ep:
                return self._reply(
                    text,
                    "I do not have any prior episode logged yet. Ask or teach me something first.",
                    intent="meta_recall",
                    mode="stored",
                    confidence=1.0,
                    record_episode=False,
                )
            proof_txt = "; ".join(last_ep.get("proof_steps", [])) or "No symbolic proof steps were required."
            recalled_n = len(last_ep.get("recalled_frame_ids", []))
            msg = (
                f"In my last episode ({last_ep['id']}), you said: \"{last_ep['user_input']}\". "
                f"I recalled {recalled_n} hypergraph frame(s) and answered: \"{last_ep['response']}\". "
                f"Reasoning trace: {proof_txt}"
            )
            return self._reply(
                text,
                msg,
                intent="meta_recall",
                mode="stored",
                confidence=1.0,
                recalled_ids=last_ep.get("recalled_frame_ids", []),
                proof_steps=last_ep.get("proof_steps", []),
                record_episode=False,
            )

        if low in {"sleep", "consolidate", "consolidate memory", "run sleep"}:
            rep = self.run_sleep_consolidation(force=True)
            msg = (
                f"Sleep consolidation complete: {rep['schemas_created']} new schema(s) distilled, "
                f"{rep['schemas_updated']} updated, {rep['pruned']} redundant raw log(s) pruned. "
                f"Total schemas: {rep['total_schemas']}."
            )
            return self._reply(
                text,
                msg,
                intent="sleep",
                mode="stored",
                confidence=1.0,
                proof_steps=["Executed offline sleep consolidation and homeostatic weight normalization."],
                record_episode=False,
            )
        return None

    def _handle_feedback_text(self, text: str) -> Optional[Dict[str, Any]]:
        low = text.lower().strip().strip(".!?")
        if low in _NEG_FEEDBACK_PHRASES or any(low.startswith(p) for p in ("that's wrong", "that is wrong", "wrong,", "wrong.", "no, that")):
            res = self.apply_feedback(positive=False)
            return self._reply(
                text,
                f"Got it — {res['message']} Tell me the right fact so I can lock it in.",
                intent="feedback_negative",
                mode="stored",
                confidence=1.0,
                proof_steps=[res["message"]],
                record_episode=False,
            )
        if low in _POS_FEEDBACK_PHRASES:
            res = self.apply_feedback(positive=True)
            return self._reply(
                text,
                f"Appreciate the confirmation — {res['message']}",
                intent="feedback_positive",
                mode="stored",
                confidence=1.0,
                proof_steps=[res["message"]],
                record_episode=False,
            )
        return None

    def _handle_forget(self, text: str) -> Optional[Dict[str, Any]]:
        m = re.match(r"^(?:forget|delete|erase)\s+(?:about\s+)?(.+?)[.!?]*$", text.strip(), re.IGNORECASE)
        if not m:
            return None
        target = _clean_phrase(m.group(1))
        removed = self.hypergraph.remove_entity(target)
        if removed > 0:
            return self._reply(
                text,
                f"Forgotten {removed} learned memory frame(s) related to '{target}'. Core identity remains protected.",
                intent="forget",
                mode="stored",
                confidence=1.0,
                proof_steps=[f"Removed {removed} non-core frames matching '{target}'."],
            )
        return self._reply(
            text,
            f"I found no removable learned memories for '{target}'.",
            intent="forget",
            mode="unknown",
            confidence=0.5,
        )

    def _handle_profile(self, text: str) -> Optional[Dict[str, Any]]:
        stripped = text.strip()
        low = stripped.lower().rstrip("?!. ")

        # Profile queries
        if low in {"what is my name", "whats my name", "what's my name", "who am i", "do you know my name"}:
            name = self.profile.get("name")
            if name:
                return self._reply(
                    stripped,
                    f"Your name is {name}.",
                    intent="profile_query",
                    mode="stored",
                    confidence=0.98,
                    proof_steps=[f"User profile lookup: name = {name}"],
                )
            return self._reply(
                stripped,
                "You have not told me your name yet. Say 'my name is ...' and I will remember it.",
                intent="profile_query",
                mode="unknown",
                confidence=0.0,
            )

        if low in {"what is my age", "how old am i", "whats my age", "what's my age"}:
            age = self.profile.get("age")
            if age:
                return self._reply(
                    stripped,
                    f"You told me you are {age} years old.",
                    intent="profile_query",
                    mode="stored",
                    confidence=0.98,
                    proof_steps=[f"User profile lookup: age = {age}"],
                )
            return self._reply(
                stripped,
                "I do not know your age yet. Tell me 'I am 18 years old' and I will store it.",
                intent="profile_query",
                mode="unknown",
                confidence=0.0,
            )

        if low in {"where do i live", "what is my city", "where am i from"}:
            loc = self.profile.get("location")
            if loc:
                return self._reply(
                    stripped,
                    f"You told me you live in {loc}.",
                    intent="profile_query",
                    mode="stored",
                    confidence=0.98,
                    proof_steps=[f"User profile lookup: location = {loc}"],
                )
            return self._reply(
                stripped,
                "You have not shared your location yet.",
                intent="profile_query",
                mode="unknown",
                confidence=0.0,
            )

        # Profile teaching
        m_name = re.match(r"^(?:my name is|call me|i am called)\s+([a-zA-Z][a-zA-Z0-9 .'-]{1,40})[.!]*$", stripped, re.IGNORECASE)
        if m_name:
            name = m_name.group(1).strip()
            self.profile["name"] = name
            fr = self.hypergraph.add_frame("HAS_NAME", "user", name, raw_text=stripped)
            return self._reply(
                stripped,
                f"Got it, {name}. I have stored your name in my memory.",
                intent="profile_teach",
                mode="stored",
                confidence=1.0,
                recalled_ids=[fr["id"]],
                proof_steps=[f"Stored user profile: name = {name}"],
                learned=[f"user HAS_NAME {name}"],
            )

        m_age = re.match(r"^(?:my age is|i am|i'm)\s+(\d{1,3})(?:\s*years?\s*old)?[.!]*$", stripped, re.IGNORECASE)
        if m_age:
            age = m_age.group(1)
            self.profile["age"] = age
            fr = self.hypergraph.add_frame("HAS_AGE", "user", age, raw_text=stripped)
            return self._reply(
                stripped,
                f"Noted — I will remember that you are {age} years old.",
                intent="profile_teach",
                mode="stored",
                confidence=1.0,
                recalled_ids=[fr["id"]],
                proof_steps=[f"Stored user profile: age = {age}"],
                learned=[f"user HAS_AGE {age}"],
            )

        m_loc = re.match(r"^(?:i live in|i am from|i'm from)\s+([a-zA-Z][a-zA-Z0-9 ,'-]{1,50})[.!]*$", stripped, re.IGNORECASE)
        if m_loc:
            loc = m_loc.group(1).strip()
            self.profile["location"] = loc
            fr = self.hypergraph.add_frame("LOCATED_IN", "user", loc, raw_text=stripped)
            return self._reply(
                stripped,
                f"Saved — you live in {loc}.",
                intent="profile_teach",
                mode="stored",
                confidence=1.0,
                recalled_ids=[fr["id"]],
                proof_steps=[f"Stored user profile: location = {loc}"],
                learned=[f"user LOCATED_IN {loc}"],
            )

        return None

    def _try_extract_local_facts(self, sentence: str) -> List[Dict[str, Any]]:
        """Extract role-bound frames from declarative English sentences."""
        s = sentence.strip().rstrip(".!")
        if not s or s.endswith("?"):
            return []
        # Skip questions even if user forgot '?'
        first_word = s.split()[0].lower()
        if first_word in {"who", "what", "where", "when", "why", "how", "can", "does", "do", "did", "is", "are"}:
            return []

        extracted: List[Dict[str, Any]] = []

        # 1. Negative capability: X cannot / can't Y
        m = re.match(r"^(.+?)\s+(?:cannot|can't|can not)\s+(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "CAN",
                "agent": _clean_phrase(m.group(1)),
                "action": "can",
                "patient": _clean_phrase(m.group(2)),
                "polarity": -1,
            })
            return extracted

        # 2. Positive capability: X can Y
        m = re.match(r"^(.+?)\s+can\s+(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "CAN",
                "agent": _clean_phrase(m.group(1)),
                "action": "can",
                "patient": _clean_phrase(m.group(2)),
                "polarity": 1,
            })
            return extracted

        # 3. Age attribute: X is 18 years old
        m = re.match(r"^(.+?)\s+is\s+(\d{1,3})\s+years?\s+old$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "HAS_AGE",
                "agent": _clean_phrase(m.group(1)),
                "action": "has_age",
                "patient": m.group(2),
                "polarity": 1,
            })
            return extracted

        # 4. Negative taxonomy: X is not a Y
        m = re.match(r"^(.+?)\s+(?:is|are)\s+not\s+(?:a|an)?\s*(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "IS_A",
                "agent": _clean_phrase(m.group(1)),
                "action": "is",
                "patient": _clean_phrase(m.group(2)),
                "polarity": -1,
            })
            return extracted

        # 5. Taxonomy / definition: X is a Y / X is Y
        m = re.match(r"^(.+?)\s+(?:is|are)\s+(a|an)\s+(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "IS_A",
                "agent": _clean_phrase(m.group(1)),
                "action": "is",
                "patient": _clean_phrase(m.group(3)),
                "polarity": 1,
            })
            return extracted

        m = re.match(r"^(.+?)\s+(?:is|are|means)\s+(.+)$", s, re.IGNORECASE)
        if m:
            ag = _clean_phrase(m.group(1))
            pat = _clean_phrase(m.group(2))
            if ag and pat and ag.lower() not in {"it", "this", "that", "there"}:
                extracted.append({
                    "relation": "DEFINED_AS",
                    "agent": ag,
                    "action": "is",
                    "patient": pat,
                    "polarity": 1,
                })
                return extracted

        # 6. Possession: X has / have Y
        m = re.match(r"^(.+?)\s+(?:has|have)\s+(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "HAS",
                "agent": _clean_phrase(m.group(1)),
                "action": "has",
                "patient": _clean_phrase(m.group(2)),
                "polarity": 1,
            })
            return extracted

        # 7. Location: X lives in / is located in Y
        m = re.match(r"^(.+?)\s+(?:lives?\s+in|located\s+in|stays?\s+in)\s+(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "LOCATED_IN",
                "agent": _clean_phrase(m.group(1)),
                "action": "lives_in",
                "patient": _clean_phrase(m.group(2)),
                "polarity": 1,
            })
            return extracted

        # 8. Creation: X created / built / made / founded Y
        m = re.match(r"^(.+?)\s+(created|built|made|founded|developed)\s+(.+)$", s, re.IGNORECASE)
        if m:
            extracted.append({
                "relation": "CREATED",
                "agent": _clean_phrase(m.group(1)),
                "action": _canon_verb(m.group(2)),
                "patient": _clean_phrase(m.group(3)),
                "polarity": 1,
            })
            return extracted

        # 9. Role-bound SVO event (solves Binding Problem: "dog bit man" != "man bit dog")
        m = re.match(
            r"^([a-zA-Z][a-zA-Z0-9 '-]{1,35}?)\s+(bit|bite|bites|ate|eats|chased|chases|killed|kills|helped|helps|loved|loves|hated|hates|liked|likes|hit|hits|saw|sees|taught|teaches|broke|fixed|wrote)\s+([a-zA-Z][a-zA-Z0-9 '-]{1,40})$",
            s,
            re.IGNORECASE,
        )
        if m:
            verb_raw = m.group(2).lower()
            extracted.append({
                "relation": "ACTION",
                "agent": _clean_phrase(m.group(1)),
                "action": _canon_verb(verb_raw),
                "patient": _clean_phrase(m.group(3)),
                "polarity": 1,
                "modifier": verb_raw,
            })
            return extracted

        return extracted

    def _answer_query(self, text: str) -> Optional[Dict[str, Any]]:
        """Proof-tracked symbolic question answering across roles, capabilities, and definitions."""
        q = text.strip().rstrip("?!. ")
        low = q.lower()

        # 1. Self & NeuraSaMu identity queries
        if any(trig in low for trig in _SELF_TRIGGERS):
            if "neurasamu" in low:
                frames = self.hypergraph.get_frames_for_agent("neurasamu")
                fids = [f["id"] for f in frames[:3]]
                return self._reply(
                    text,
                    "NeuraSaMu is an independent AI research and software development lab founded by Muhammad Salman Shar (neurasamu.com), focused on neuro-symbolic intelligence like NSM VB.",
                    intent="self_query",
                    mode="stored",
                    confidence=0.99,
                    recalled_ids=fids,
                    proof_steps=["Core identity recall: NeuraSaMu -> independent AI lab founded by Muhammad Salman Shar."],
                )
            if any(w in low for w in ("made", "created", "built", "creator", "founder")):
                frames = self.hypergraph.get_frames_for_agent("muhammad salman shar")
                fids = [f["id"] for f in frames[:3]]
                return self._reply(
                    text,
                    "I was created by Muhammad Salman Shar (Salman / Akira), the founder of NeuraSaMu.",
                    intent="self_query",
                    mode="stored",
                    confidence=0.99,
                    recalled_ids=fids,
                    proof_steps=["Core identity recall: Muhammad Salman Shar CREATED NSM VB."],
                )
            frames = self.hypergraph.get_frames_for_agent("nsm vb")
            fids = [f["id"] for f in frames[:3]]
            return self._reply(
                text,
                "I am NSM VB v1.4, a neuro-symbolic virtual brain built by Muhammad Salman Shar at NeuraSaMu. I learn role-bound facts, track my own reasoning traces, evolve through surgical feedback, and consolidate memory offline.",
                intent="self_query",
                mode="stored",
                confidence=0.99,
                recalled_ids=fids,
                proof_steps=["Core identity recall: NSM VB v1.4 cognitive architecture."],
            )

        # 2. Capability query: "Can X Y?" (Defeasible inheritance + strict boundary enforcement)
        m = re.match(r"^can\s+(.+?)\s+([a-zA-Z][a-zA-Z0-9 '-]*)$", q, re.IGNORECASE)
        if m:
            subj = _clean_phrase(m.group(1))
            ability = _clean_phrase(m.group(2))
            disp_subj = _display_entity(subj)
            res = self.hypergraph.query_capability_or_relation(subj, "CAN", ability)
            if res["mode"] == "contradicted":
                return self._reply(
                    text,
                    f"My memory holds conflicting evidence on whether {disp_subj} can {ability}. Tell me which one is correct to resolve it.",
                    intent="query_can",
                    mode="contradicted",
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            if res["mode"] in {"stored", "derived"}:
                pol = res["polarity"]
                basis = "directly stored" if res["mode"] == "stored" else "derived via inheritance"
                pct = round(res["confidence"] * 100)
                if pol > 0:
                    ans = f"Yes, {disp_subj} can {ability} ({basis}, confidence {pct}%)."
                else:
                    ans = f"No, {disp_subj} cannot {ability} ({basis}, confidence {pct}%)."
                return self._reply(
                    text,
                    ans,
                    intent="query_can",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            # Strict boundary: never hijack an unknown capability query with another entity's vector hit
            proofs = [f"Boundary check: no stored or inherited CAN frame links '{normalize_entity(subj)}' to '{normalize_entity(ability)}'."]
            note = ""
            alt_hits = self.hypergraph.semantic_search(ability, top_k=3, min_score=0.35)
            for alt_fr, alt_sc in alt_hits:
                if alt_fr.get("relation") == "CAN" and alt_fr.get("polarity", 1) > 0 and alt_fr.get("agent") != normalize_entity(subj):
                    note = f" However, my memory shows that {self._frame_to_sentence(alt_fr)}"
                    proofs.append(f"Contrast note ({alt_sc:.2f}): {alt_fr['agent']} CAN {alt_fr['patient']}")
                    break
            return self._reply(
                text,
                f"I have no stored evidence that {disp_subj} can {ability}.{note}",
                intent="query_can",
                mode="unknown",
                confidence=0.0,
                recalled_ids=[],
                proof_steps=proofs,
            )

        # 3. Role-bound SVO Agent query: "Who bit man?" / "What chased cat?"
        m = re.match(r"^(?:who|what)\s+([a-zA-Z]+)\s+(.+)$", q, re.IGNORECASE)
        if m and m.group(1).lower() not in {"is", "are", "was", "were", "did", "does", "do", "has", "have", "can"}:
            verb = _canon_verb(m.group(1))
            patient = _clean_phrase(m.group(2))
            pat_frames = self.hypergraph.get_frames_for_patient(patient)
            matches = [
                f for f in pat_frames
                if _canon_verb(f.get("action", "")) == verb or (verb == "create" and f.get("relation") == "CREATED")
            ]
            if matches:
                top = matches[0]
                verb_surface = top.get("modifier") or top.get("action") or m.group(1)
                conf = self.hypergraph.bayesian_confidence(top)
                return self._reply(
                    text,
                    f"{top['agent'].title()} {verb_surface} {top['patient']}.",
                    intent="query_role_agent",
                    mode="stored",
                    confidence=conf,
                    recalled_ids=[top["id"]],
                    proof_steps=[f"Role-bound match: Agent={top['agent']}, Action={top['action']}, Patient={top['patient']}"],
                )

        # 4. Role-bound SVO Patient query: "Who/What did X <verb>?"
        m = re.match(r"^(?:who|what)\s+(?:did|does)\s+(.+?)\s+([a-zA-Z]+)$", q, re.IGNORECASE)
        if m:
            agent = _clean_phrase(m.group(1))
            verb = _canon_verb(m.group(2))
            ag_frames = self.hypergraph.get_frames_for_agent(agent)
            matches = [
                f for f in ag_frames
                if _canon_verb(f.get("action", "")) == verb or (verb == "create" and f.get("relation") == "CREATED")
            ]
            if matches:
                top = matches[0]
                verb_surface = top.get("modifier") or top.get("action") or m.group(2)
                conf = self.hypergraph.bayesian_confidence(top)
                return self._reply(
                    text,
                    f"{top['agent'].title()} {verb_surface} {top['patient']}.",
                    intent="query_role_patient",
                    mode="stored",
                    confidence=conf,
                    recalled_ids=[top["id"]],
                    proof_steps=[f"Role-bound match: Agent={top['agent']}, Action={top['action']}, Patient={top['patient']}"],
                )

        # 5. Age query: "How old is X?"
        m = re.match(r"^how\s+old\s+is\s+(.+)$", q, re.IGNORECASE)
        if m:
            subj = _clean_phrase(m.group(1))
            res = self.hypergraph.query_capability_or_relation(subj, "HAS_AGE")
            if res["mode"] in {"stored", "derived"} and res["frames"]:
                val = res["frames"][0]["patient"]
                return self._reply(
                    text,
                    f"{subj.title()} is {val} years old.",
                    intent="query_age",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )

        # 6. Location query: "Where does X live?"
        m = re.match(r"^where\s+(?:does|is)\s+(.+?)(?:\s+live|\s+located)?$", q, re.IGNORECASE)
        if m:
            subj = _clean_phrase(m.group(1))
            res = self.hypergraph.query_capability_or_relation(subj, "LOCATED_IN")
            if res["mode"] in {"stored", "derived"} and res["frames"]:
                val = res["frames"][0]["patient"]
                return self._reply(
                    text,
                    f"{subj.title()} lives in {val}.",
                    intent="query_location",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )

        # 7. Definition / Topic query: "What is X?" / "Who is X?" / compound questions
        m = re.match(r"^(?:what|who)\s+(?:is|are)\s+(.+)$", q, re.IGNORECASE)
        if not m:
            m = re.match(r"^(?:tell me about|explain|define|describe)\s+(.+)$", q, re.IGNORECASE)
        if m:
            raw_topic = m.group(1)
            # Handle compound phrasing like "a hash table and what is it a type of"
            primary_part = re.split(r"\s+(?:and|or)\s+(?:what|who|how|why|where)\b", raw_topic, maxsplit=1, flags=re.IGNORECASE)[0]
            topic = _clean_phrase(primary_part)
            frames = self.hypergraph.get_frames_for_agent(topic)
            if frames:
                return self._summarize_entity_frames(text, topic, frames)
            rev_frames = self.hypergraph.get_frames_for_patient(topic)
            if rev_frames:
                return self._summarize_entity_frames(text, topic, rev_frames)
            # Longest known entity match inside the query text
            known_agents = sorted(self.hypergraph._by_agent.keys(), key=len, reverse=True)
            q_low = low
            for ent in known_agents:
                if len(ent) >= 2 and re.search(r"\b" + re.escape(ent) + r"\b", q_low):
                    ent_frames = self.hypergraph.get_frames_for_agent(ent)
                    if ent_frames:
                        return self._summarize_entity_frames(text, ent, ent_frames)

        # 8. Bare topic query (1-3 words matching a known entity)
        if len(q.split()) <= 3:
            topic = _clean_phrase(q)
            frames = self.hypergraph.get_frames_for_agent(topic)
            if frames:
                return self._summarize_entity_frames(text, topic, frames)

        # 9. Semantic vector recall across hypergraph & past episodes (handles paraphrases!)
        sem_hits = self.hypergraph.semantic_search(q, top_k=4, min_score=0.28)
        if sem_hits:
            top_frames = [fr for fr, _ in sem_hits[:3]]
            top_score = sem_hits[0][1]
            snippets = [self._frame_to_sentence(fr) for fr in top_frames]
            fids = [fr["id"] for fr in top_frames]
            proofs = [
                f"Vector recall ({sc:.2f}): {fr['agent']} {fr['relation']} {fr['patient']}"
                for fr, sc in sem_hits[:3]
            ]
            return self._reply(
                text,
                " ".join(snippets),
                intent="semantic_recall",
                mode="stored",
                confidence=min(0.95, max(0.45, top_score)),
                recalled_ids=fids,
                proof_steps=proofs,
            )

        # Check episodic recall if user is asking something similar to a past conversation
        ep_hits = self.episodic.recall_similar(q, top_k=2, min_score=0.38)
        if ep_hits:
            best_ep, ep_score = ep_hits[0]
            if best_ep.get("response") and best_ep.get("mode") != "unknown":
                return self._reply(
                    text,
                    f"From a similar earlier episode: {best_ep['response']}",
                    intent="episodic_recall",
                    mode="derived",
                    confidence=round(ep_score * 0.85, 3),
                    recalled_ids=best_ep.get("recalled_frame_ids", []),
                    proof_steps=[f"Matched prior episode {best_ep['id']} (sim={ep_score:.2f})."],
                )

        return None

    @staticmethod
    def _frame_to_sentence(fr: Dict[str, Any]) -> str:
        ag = _display_entity(fr.get("agent", ""))
        pat = fr.get("patient", "")
        rel = fr.get("relation", "")
        pol = fr.get("polarity", 1)
        if rel == "IS_A":
            return f"{ag} is {'not ' if pol < 0 else ''}a {pat}."
        if rel == "DEFINED_AS":
            return f"{ag} is {'not ' if pol < 0 else ''}{pat}."
        if rel == "CAN":
            return f"{ag} {'can' if pol > 0 else 'cannot'} {pat}."
        if rel == "HAS":
            return f"{ag} has {pat}."
        if rel == "HAS_AGE":
            return f"{ag} is {pat} years old."
        if rel == "LOCATED_IN":
            return f"{ag} lives in {pat}."
        if rel == "CREATED":
            act = fr.get("action") or "created"
            return f"{ag} {act} {pat}."
        if rel == "ACTION":
            act = fr.get("modifier") or fr.get("action") or "acted on"
            return f"{ag} {act} {pat}."
        return f"{ag} {rel.lower().replace('_', ' ')} {pat}."

    def _summarize_entity_frames(self, query: str, topic: str, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        selected = frames[:4]
        sentences = [self._frame_to_sentence(fr) for fr in selected]
        fids = [fr["id"] for fr in selected]
        avg_conf = sum(self.hypergraph.bayesian_confidence(fr) for fr in selected) / len(selected)
        proofs = [
            f"Hypergraph node '{topic}': {fr['agent']} {fr['relation']} {fr['patient']} (conf={self.hypergraph.bayesian_confidence(fr)})"
            for fr in selected
        ]
        return self._reply(
            query,
            " ".join(sentences),
            intent="topic_query",
            mode="stored",
            confidence=avg_conf,
            recalled_ids=fids,
            proof_steps=proofs,
        )

    def observe_bulk(
        self,
        text: str,
        llm_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main cognitive turn entrypoint: process user message, learn or reason, and optionally polish via Samu Lab API."""
        cleaned = (text or "").strip()
        if not cleaned:
            return self._reply("", "Please type a message so I can think or learn.", "empty", "unknown", 0.0, record_episode=False)

        low = cleaned.lower().strip(" .!?")

        # 1. Greetings
        if low in _GREETINGS:
            user_name = self.profile.get("name")
            greet = f"Hello{', ' + user_name if user_name else ''}! NSM VB v1.4 is online. Teach me something new or ask me anything."
            return self._reply(cleaned, greet, "greeting", "stored", 1.0, record_episode=False)

        # 2. Meta-memory recall & sleep command
        meta_res = self._handle_meta_recall(cleaned)
        if meta_res:
            return meta_res

        # 3. Direct textual feedback (Surgical Credit Assignment)
        fb_res = self._handle_feedback_text(cleaned)
        if fb_res:
            return fb_res

        # 4. Forget command
        forget_res = self._handle_forget(cleaned)
        if forget_res:
            return forget_res

        # 5. User profile statements / queries
        prof_res = self._handle_profile(cleaned)
        if prof_res:
            return prof_res

        # 6. Check if the input contains declarative facts to learn (supports multi-sentence bulk teaching)
        parts = [p.strip() for p in re.split(r"(?<=[.!?;])\s+|\n+", cleaned) if p.strip()]
        learned_frames: List[Dict[str, Any]] = []
        learned_summaries: List[str] = []
        rejected_notes: List[str] = []
        question_parts: List[str] = []

        for part in parts:
            if part.endswith("?") or part.split()[0].lower() in {"who", "what", "where", "when", "why", "how", "can", "does", "do", "did"}:
                question_parts.append(part)
                continue
            facts = self._try_extract_local_facts(part)
            for fc in facts:
                try:
                    fr = self.hypergraph.add_frame(
                        relation=fc["relation"],
                        agent=fc["agent"],
                        patient=fc["patient"],
                        action=fc.get("action", ""),
                        modifier=fc.get("modifier", ""),
                        polarity=int(fc.get("polarity", 1)),
                        source="user",
                        raw_text=part,
                    )
                    learned_frames.append(fr)
                    learned_summaries.append(self._frame_to_sentence(fr))
                except ValueError as ve:
                    rejected_notes.append(str(ve))

        # If both facts and a question were given in one turn, answer the question after learning
        if question_parts:
            q_res = self._answer_query(question_parts[-1])
            if q_res:
                if learned_summaries:
                    q_res["learned"] = learned_summaries
                    q_res["response"] = f"Learned {len(learned_summaries)} fact(s). " + q_res["response"]
                return self._maybe_enhance_with_cortex(cleaned, q_res, llm_url, llm_model, llm_key)

        # Pure teaching turn
        if learned_frames and not question_parts:
            fids = [f["id"] for f in learned_frames]
            proofs = [f"Stored role-bound frame: {f['agent']} {f['relation']} {f['patient']} (pol={f['polarity']})" for f in learned_frames]
            if len(learned_summaries) == 1:
                reply_text = f"Learned and bound in memory: {learned_summaries[0]}"
            else:
                reply_text = f"Learned {len(learned_summaries)} structured facts: " + " ".join(learned_summaries[:4])
            res = self._reply(
                cleaned,
                reply_text,
                intent="teach",
                mode="stored",
                confidence=0.95,
                recalled_ids=fids,
                proof_steps=proofs,
                learned=learned_summaries,
            )
            return self._maybe_enhance_with_cortex(cleaned, res, llm_url, llm_model, llm_key)

        if rejected_notes and not question_parts:
            return self._reply(
                cleaned,
                f"I skipped that because: {rejected_notes[0]}",
                intent="reject",
                mode="unknown",
                confidence=0.9,
                proof_steps=rejected_notes,
            )

        # 7. Symbolic query & vector/episodic recall
        q_res = self._answer_query(cleaned)
        if q_res:
            return self._maybe_enhance_with_cortex(cleaned, q_res, llm_url, llm_model, llm_key)

        # 8. Optional Samu Lab API Cortex fallback: sarcasm check + fact extraction + grounded chat
        if llm_url and llm_model:
            analysis = cortex_api.analyze_with_cortex(cleaned, llm_url, llm_model, llm_key)
            if analysis:
                if analysis.get("is_sarcastic") and analysis.get("sentiment") == "negative":
                    fb = self.apply_feedback(positive=False)
                    return self._reply(
                        cleaned,
                        f"Caught the sarcasm — {fb['message']} Let me know the correct detail.",
                        intent="feedback_negative",
                        mode="stored",
                        confidence=0.9,
                        proof_steps=["Cortex detected sarcastic negative feedback.", fb["message"]],
                        cortex_used=True,
                        record_episode=False,
                    )
                api_facts = analysis.get("facts") or []
                api_learned: List[str] = []
                api_fids: List[str] = []
                for fc in api_facts[:5]:
                    if not isinstance(fc, dict):
                        continue
                    ag = _clean_phrase(str(fc.get("agent", "")))
                    pat = _clean_phrase(str(fc.get("patient", "")))
                    if ag and pat:
                        try:
                            fr = self.hypergraph.add_frame(
                                relation=str(fc.get("relation", "RELATED_TO")),
                                agent=ag,
                                patient=pat,
                                action=str(fc.get("action", "")),
                                polarity=int(fc.get("polarity", 1)),
                                source="cortex",
                                raw_text=cleaned,
                            )
                            api_fids.append(fr["id"])
                            api_learned.append(self._frame_to_sentence(fr))
                        except ValueError:
                            pass
                if api_learned:
                    base_ans = "Learned via Cortex parsing: " + " ".join(api_learned)
                    res = self._reply(
                        cleaned,
                        base_ans,
                        intent="teach",
                        mode="stored",
                        confidence=0.88,
                        recalled_ids=api_fids,
                        proof_steps=["Samu Lab Cortex extracted structured role-filler facts."],
                        learned=api_learned,
                        cortex_used=True,
                    )
                    return self._maybe_enhance_with_cortex(cleaned, res, llm_url, llm_model, llm_key)

        # 9. Honest unknown response (with optional Cortex conversational help)
        unknown_res = self._reply(
            cleaned,
            "I do not have that in my memory yet. Teach me with a clear statement (for example: 'X is a Y' or 'X can Y') and I will store and reason with it.",
            intent="unknown",
            mode="unknown",
            confidence=0.0,
            proof_steps=["No direct, inherited, or semantic match found in hypergraph."],
        )
        return self._maybe_enhance_with_cortex(cleaned, unknown_res, llm_url, llm_model, llm_key)

    def _maybe_enhance_with_cortex(
        self,
        user_text: str,
        result: Dict[str, Any],
        llm_url: Optional[str],
        llm_model: Optional[str],
        llm_key: Optional[str],
    ) -> Dict[str, Any]:
        if not llm_url or not llm_model:
            return result
        # Gather short context snippets from recalled frames
        recalled_ctx = []
        for fid in result.get("recalled_frame_ids", [])[:4]:
            fr = self.hypergraph.frames.get(fid)
            if fr:
                recalled_ctx.append(self._frame_to_sentence(fr))

        polished = cortex_api.realize_with_cortex(
            user_text=user_text,
            symbolic_answer=result["response"],
            proof_steps=result.get("proof_steps", []),
            recalled_context=recalled_ctx,
            mode=result.get("mode", "stored"),
            llm_url=llm_url,
            llm_model=llm_model,
            llm_key=llm_key,
        )
        if polished:
            result["response"] = polished
            result["cortex_used"] = True
            # Keep the latest episode response synchronized with polished reply
            if self.episodic.episodes and self.episodic.episodes[-1].get("id") == result.get("episode_id"):
                self.episodic.episodes[-1]["response"] = polished[:500]
        return result

    def state(self) -> Dict[str, Any]:
        last_ep = self.episodic.get_last_episode(skip_meta=True)
        return {
            "version": self.version,
            "engine": "NSM VB v1.4 (NeuraSaMu)",
            "frames": len(self.hypergraph.frames),
            "senses": len(self.hypergraph.senses),
            "episodes": len(self.episodic.episodes),
            "schemas": len(self.episodic.schemas),
            "total_consolidated": self.episodic.total_consolidated_episodes,
            "turn_count": self.turn_count,
            "profile": self.profile,
            "last_episode": {
                "id": last_ep.get("id"),
                "mode": last_ep.get("mode"),
                "confidence": last_ep.get("confidence"),
                "proof_steps": last_ep.get("proof_steps", []),
            } if last_ep else None,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nsm_version": self.VERSION,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turn_count": self.turn_count,
            "profile": self.profile,
            "hypergraph": self.hypergraph.to_dict(),
            "episodic": self.episodic.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Brain":
        brain = cls(seed_core=True)
        if not isinstance(data, dict):
            return brain

        # Native v1.4 load
        if data.get("nsm_version") == "1.4":
            brain.created_at = float(data.get("created_at", brain.created_at))
            brain.updated_at = float(data.get("updated_at", brain.updated_at))
            brain.turn_count = int(data.get("turn_count", 0))
            if isinstance(data.get("profile"), dict):
                brain.profile.update(data["profile"])
            loaded_hg = TypedHypergraph.from_dict(data.get("hypergraph"))
            for sid, sdata in loaded_hg.senses.items():
                brain.hypergraph.senses[sid] = sdata
            for fid, fr in loaded_hg.frames.items():
                brain.hypergraph.frames[fid] = fr
                brain.hypergraph._index_frame_in_ram(fr)
            brain.episodic = EpisodicMemory.from_dict(data.get("episodic"))
            return brain

        # Legacy NSM v1.x auto-migration (facts / relations / memory)
        brain._migrate_legacy(data)
        return brain

    def _migrate_legacy(self, data: Dict[str, Any]) -> None:
        """Import older NSM v1.x JSON brain exports cleanly into v1.4 hypergraph."""
        # Migrate legacy relations list/dict
        rels = data.get("relations")
        if isinstance(rels, list):
            for item in rels[:1500]:
                if isinstance(item, dict):
                    s = item.get("subject") or item.get("src") or item.get("s")
                    r = item.get("relation") or item.get("rel") or item.get("type") or "RELATED_TO"
                    o = item.get("object") or item.get("dst") or item.get("o")
                    pol = -1 if str(r).upper() in {"CANNOT", "IS_NOT"} else 1
                    norm_r = "CAN" if str(r).upper() == "CANNOT" else str(r).upper()
                    if s and o:
                        try:
                            self.hypergraph.add_frame(norm_r, str(s), str(o), polarity=pol, source="imported")
                        except ValueError:
                            pass
        elif isinstance(rels, dict):
            for key, vals in rels.items():
                if isinstance(vals, list):
                    for item in vals[:300]:
                        if isinstance(item, dict):
                            r = item.get("relation") or item.get("rel") or "RELATED_TO"
                            o = item.get("object") or item.get("target") or item.get("o")
                            if o:
                                try:
                                    self.hypergraph.add_frame(str(r), str(key), str(o), source="imported")
                                except ValueError:
                                    pass

        # Migrate legacy flat facts dict
        facts = data.get("facts")
        if isinstance(facts, dict):
            for k, v in list(facts.items())[:500]:
                if isinstance(v, (str, int, float)):
                    if k.lower() in {"name", "user_name"}:
                        self.profile["name"] = str(v)
                    elif k.lower() in {"age", "user_age"}:
                        self.profile["age"] = str(v)
                    else:
                        try:
                            self.hypergraph.add_frame("DEFINED_AS", str(k), str(v), source="imported")
                        except ValueError:
                            pass
