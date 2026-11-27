"""NSM VB v1.5 - NeuraSaMu Neuro-Symbolic Cognitive Brain (Pure English Core).

Core Architecture:
1. Compositional English Language Parser (16 question types x 14 relations,
   conversational wrapper stripping, active-topic coreference, portable JSON extensions).
2. Typed Role-Filler Hypergraph (binding-safe, sense-disambiguated, Bayesian confidence,
   alias resolution, causal/consequence/comparison/verification/examples reasoning).
3. Natural Conversational English Realizer (context-aware, zero robotic boilerplate).
4. Episodic Recall Trace + Surgical Credit Assignment + Offline Sleep Consolidation.
5. Future-proof Portable Contract (v1.5 brain + skills + language_extensions + MCP slots).
"""

import re
import time
from typing import Any, Dict, List, Optional

from src import cortex_api, realizer, skills as skill_engine
from src.episodic import EpisodicMemory
from src.hypergraph import TypedHypergraph, normalize_entity, tokenize_content
from src.parser import CompositionalParser, ParsedQuestion, canon_verb, clean_phrase, is_valid_agent

_GREETINGS = frozenset({
    "hi", "hello", "hey", "yo", "hola", "salam", "assalam", "assalamualaikum",
    "good morning", "good evening", "good afternoon", "gm", "sup",
})

_NEG_FEEDBACK_PHRASES = (
    "that's wrong", "that is wrong", "you are wrong", "wrong answer",
    "incorrect", "nope wrong", "no that's wrong", "not right",
    "bad answer", "false",
)

_POS_FEEDBACK_PHRASES = (
    "good job", "correct", "that's right", "that is right", "exact",
    "spot on", "well done", "nice answer", "perfect",
)

_SELF_TRIGGERS = (
    "who are you", "what are you", "your name", "who made you",
    "who created you", "who built you", "about yourself", "tell me about you",
    "what is nsm", "who is your creator", "who is your founder",
    "what is neurasamu", "tell me about neurasamu",
)

_CREATOR_VERBS = frozenset({"create", "make", "build", "found", "develop", "invent", "design"})


class Brain:
    """NSM VB v1.5 cognitive engine."""

    VERSION = "1.5"

    def __init__(self, seed_core: bool = True):
        self.version = self.VERSION
        self.hypergraph = TypedHypergraph(max_hot_frames=5000)
        self.episodic = EpisodicMemory(max_raw_episodes=180)
        self.profile: Dict[str, str] = {}
        self.active_topic: Optional[str] = None
        self.skills: Dict[str, Any] = {"installed": {}, "mcp_servers": {}}
        self.language_extensions: Dict[str, Any] = {"custom_patterns": []}
        self.parser = CompositionalParser()
        self.created_at: float = time.time()
        self.updated_at: float = self.created_at
        self.turn_count: int = 0
        if seed_core:
            self._seed_core_knowledge()

    def _seed_core_knowledge(self) -> None:
        """Seed immutable core NeuraSaMu & NSM VB v1.5 identity knowledge."""
        core_facts = [
            ("IS_A", "nsm vb", "neuro-symbolic virtual brain", "", 1, "NSM VB is a neuro-symbolic virtual brain built by NeuraSaMu."),
            ("DEFINED_AS", "nsm vb", "version 1.5 cognitive architecture with compositional English understanding, typed hypergraph reasoning, episodic recall trace, surgical credit assignment, and sleep consolidation", "", 1, "NSM VB v1.5 architecture overview."),
            ("ALSO_KNOWN_AS", "nsm vb", "nsm", "", 1, "NSM VB is also known as NSM."),
            ("CREATED", "muhammad salman shar", "nsm vb", "created", 1, "Muhammad Salman Shar created NSM VB."),
            ("CREATED", "muhammad salman shar", "neurasamu", "founded", 1, "Muhammad Salman Shar founded NeuraSaMu."),
            ("IS_A", "muhammad salman shar", "founder of neurasamu and creator of nsm vb", "", 1, "Muhammad Salman Shar (Salman / Akira) is the founder of NeuraSaMu."),
            ("IS_A", "neurasamu", "independent ai research and software development lab", "", 1, "NeuraSaMu is an independent AI research and software lab at neurasamu.com."),
            ("HAS", "neurasamu", "official website neurasamu.com", "", 1, "NeuraSaMu website is neurasamu.com."),
            ("CAN", "nsm vb", "learn role-bound facts, reason across 16 question types, explain proof traces, recall past episodes, and consolidate memory offline", "", 1, "NSM VB core capabilities."),
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
            "active_topic": self.active_topic,
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
        target = clean_phrase(m.group(1))
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

    def _handle_self_query(self, text: str) -> Optional[Dict[str, Any]]:
        low = text.lower().strip().rstrip("?!. ")
        if not any(trig in low for trig in _SELF_TRIGGERS):
            return None

        if "neurasamu" in low:
            frames = self.hypergraph.get_frames_for_agent("neurasamu")
            fids = [f["id"] for f in frames[:3]]
            self.active_topic = "neurasamu"
            msg = (
                "NeuraSaMu is an independent AI research and software development lab founded by "
                "Muhammad Salman Shar (neurasamu.com), focused on neuro-symbolic intelligence like NSM VB."
            )
            return self._reply(
                text, msg, intent="self_query", mode="stored", confidence=0.99,
                recalled_ids=fids,
                proof_steps=["Core identity recall: NeuraSaMu -> independent AI lab founded by Muhammad Salman Shar."],
            )

        if any(w in low for w in ("made", "created", "built", "creator", "founder")):
            frames = self.hypergraph.get_frames_for_agent("muhammad salman shar")
            fids = [f["id"] for f in frames[:3]]
            self.active_topic = "muhammad salman shar"
            msg = "I was created by Muhammad Salman Shar (Salman / Akira), the founder of NeuraSaMu."
            return self._reply(
                text, msg, intent="self_query", mode="stored", confidence=0.99,
                recalled_ids=fids,
                proof_steps=["Core identity recall: Muhammad Salman Shar CREATED NSM VB."],
            )

        frames = self.hypergraph.get_frames_for_agent("nsm vb")
        fids = [f["id"] for f in frames[:3]]
        self.active_topic = "nsm vb"
        msg = (
            "I am NSM VB v1.5, a neuro-symbolic virtual brain built by Muhammad Salman Shar at NeuraSaMu. "
            "I learn role-bound facts in English, reason across 16 question types with proof traces, and consolidate memory offline."
        )
        return self._reply(
            text, msg, intent="self_query", mode="stored", confidence=0.99,
            recalled_ids=fids,
            proof_steps=["Core identity recall: NSM VB v1.5 cognitive architecture."],
        )

    def _summarize_entity_frames(
        self,
        query: str,
        topic: str,
        frames: List[Dict[str, Any]],
        intent: str = "topic_query",
    ) -> Dict[str, Any]:
        prio = {"DEFINED_AS": 0, "IS_A": 1, "USED_FOR": 2, "WORKS_BY": 3, "ALSO_KNOWN_AS": 4}
        ordered = sorted(
            frames,
            key=lambda f: (prio.get(f.get("relation", ""), 9), -self.hypergraph.bayesian_confidence(f)),
        )
        selected = ordered[:4]
        self.active_topic = topic
        response_txt = realizer.realize_frames(selected, max_items=4)
        fids = [fr["id"] for fr in selected]
        avg_conf = sum(self.hypergraph.bayesian_confidence(fr) for fr in selected) / len(selected)
        proofs = [
            f"Hypergraph node '{topic}': {fr['agent']} {fr['relation']} {fr['patient']} (conf={self.hypergraph.bayesian_confidence(fr)})"
            for fr in selected
        ]
        return self._reply(
            query,
            response_txt,
            intent=intent,
            mode="stored",
            confidence=avg_conf,
            recalled_ids=fids,
            proof_steps=proofs,
        )

    def _dispatch_question(self, pq: ParsedQuestion, full_text: str) -> Optional[Dict[str, Any]]:
        """Route any of the 16 structured ParsedQuestion types through typed hypergraph reasoning."""
        qtype = pq.qtype

        # 0. Self / NeuraSaMu identity shortcut
        self_res = self._handle_self_query(pq.raw_text)
        if self_res:
            return self_res

        # 16. FOLLOW-UP / ELABORATION
        if qtype == "QUERY_FOLLOWUP":
            topic = self.hypergraph.resolve_alias(pq.subject or self.active_topic or "")
            if not topic:
                return self._reply(
                    full_text,
                    "There is no active topic yet — ask or teach me about something first!",
                    intent="query_followup", mode="unknown", confidence=0.0,
                )
            all_frames = self.hypergraph.get_frames_for_agent(topic)
            last_ep = self.episodic.get_last_episode(skip_meta=True)
            already_shown = set(last_ep.get("recalled_frame_ids", [])) if last_ep else set()
            unseen = [f for f in all_frames if f["id"] not in already_shown]
            if unseen:
                return self._summarize_entity_frames(full_text, topic, unseen, intent="query_followup")
            if all_frames:
                disp = realizer.display_entity(topic)
                return self._reply(
                    full_text,
                    f"That is everything I currently have stored about {disp}. Teach me another detail and I will link it in.",
                    intent="query_followup", mode="stored", confidence=0.85,
                    recalled_ids=[f["id"] for f in all_frames[:2]],
                    proof_steps=[f"Follow-up checked all {len(all_frames)} frames on active topic '{topic}'."],
                )
            return self._reply(
                full_text, realizer.realize_unknown(qtype, topic),
                intent="query_followup", mode="unknown", confidence=0.0,
            )

        # 12. COMPARISON / CONTRAST
        if qtype == "QUERY_COMPARE":
            comp = self.hypergraph.compare_entities(pq.subject, pq.secondary_subject)
            if comp["entity_a"]:
                self.active_topic = comp["entity_a"]
            return self._reply(
                full_text,
                realizer.realize_comparison(comp),
                intent="query_compare",
                mode=comp["mode"],
                confidence=comp["confidence"],
                recalled_ids=comp["used_frame_ids"],
                proof_steps=comp["proof_steps"],
            )

        # 6. CHOICE / ALTERNATIVE
        if qtype == "QUERY_CHOICE" and len(pq.options) >= 2:
            opt_a, opt_b = pq.options[0], pq.options[1]
            if pq.subject:
                subj = self.hypergraph.resolve_alias(pq.subject)
                self.active_topic = subj
                res_a = self.hypergraph.query_verify(subj, "IS_A", opt_a)
                res_b = self.hypergraph.query_verify(subj, "IS_A", opt_b)
                used = list(dict.fromkeys(res_a.get("used_frame_ids", []) + res_b.get("used_frame_ids", [])))
                proofs = res_a.get("proof_steps", []) + res_b.get("proof_steps", [])
                best_conf = max(res_a.get("confidence", 0.0), res_b.get("confidence", 0.0))
                mode = "stored" if (res_a["mode"] in {"stored", "derived"} or res_b["mode"] in {"stored", "derived"}) else "unknown"
                ans = realizer.realize_choice(subj, opt_a, opt_b, res_a, res_b)
                return self._reply(
                    full_text, ans, intent="query_choice", mode=mode,
                    confidence=best_conf, recalled_ids=used, proof_steps=proofs,
                )
            comp = self.hypergraph.compare_entities(opt_a, opt_b)
            return self._reply(
                full_text, realizer.realize_comparison(comp), intent="query_choice", mode=comp["mode"],
                confidence=comp["confidence"], recalled_ids=comp["used_frame_ids"],
                proof_steps=comp["proof_steps"],
            )

        # 8. CONSEQUENCE / HYPOTHETICAL
        if qtype == "QUERY_IF_THEN":
            res = self.hypergraph.query_consequence(pq.subject)
            if res["mode"] != "unknown":
                return self._reply(
                    full_text,
                    realizer.realize_frames(res["frames"], max_items=3),
                    intent="query_if_then",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            return self._reply(
                full_text, realizer.realize_unknown(qtype, pq.subject),
                intent="query_if_then", mode="unknown", confidence=0.0,
                proof_steps=res["proof_steps"],
            )

        # 7. CAUSAL (WHY / REASON)
        if qtype == "QUERY_CAUSE":
            res = self.hypergraph.query_causal(pq.subject)
            if res["mode"] != "unknown":
                self.active_topic = pq.subject
                return self._reply(
                    full_text,
                    realizer.realize_frames(res["frames"], max_items=3),
                    intent="query_cause",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            return self._reply(
                full_text, realizer.realize_unknown(qtype, pq.subject),
                intent="query_cause", mode="unknown", confidence=0.0,
                proof_steps=res["proof_steps"],
            )

        # 10. PURPOSE / UTILITY
        if qtype == "QUERY_PURPOSE":
            subj = self.hypergraph.resolve_alias(pq.subject)
            res = self.hypergraph.query_capability_or_relation(subj, "USED_FOR")
            if res["mode"] == "unknown":
                res = self.hypergraph.query_capability_or_relation(subj, "CAN")
            if res["mode"] in {"stored", "derived"} and res["frames"]:
                self.active_topic = subj
                return self._reply(
                    full_text,
                    realizer.realize_frames(res["frames"], max_items=3),
                    intent="query_purpose",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            return self._reply(
                full_text, realizer.realize_unknown(qtype, subj),
                intent="query_purpose", mode="unknown", confidence=0.0,
                proof_steps=[f"No USED_FOR or CAN frame found for '{subj}'."],
            )

        # 9. PROCEDURAL (HOW IT WORKS)
        if qtype == "QUERY_HOW":
            subj = self.hypergraph.resolve_alias(pq.subject)
            res = self.hypergraph.query_capability_or_relation(subj, "WORKS_BY")
            if res["mode"] in {"stored", "derived"} and res["frames"]:
                self.active_topic = subj
                return self._reply(
                    full_text,
                    realizer.realize_frames(res["frames"], max_items=3),
                    intent="query_how",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            defs = self.hypergraph.get_frames_for_agent(subj, relation="DEFINED_AS")
            if defs:
                return self._summarize_entity_frames(full_text, subj, defs[:2], intent="query_how")
            return self._reply(
                full_text, realizer.realize_unknown(qtype, subj),
                intent="query_how", mode="unknown", confidence=0.0,
                proof_steps=[f"No WORKS_BY frame found for '{subj}'."],
            )

        # 11. COMPOSITION / PARTS / BRANCHES
        if qtype == "QUERY_PARTS":
            subj = self.hypergraph.resolve_alias(pq.subject)
            attr_word = (pq.target or "parts").lower()
            frames = (
                self.hypergraph.get_frames_for_agent(subj, relation="HAS_BRANCHES")
                if attr_word in {"branches", "types", "kinds", "fields", "categories"}
                else []
            )
            frames = frames + self.hypergraph.get_frames_for_agent(subj, relation="HAS_PART")
            if not frames:
                frames = self.hypergraph.get_frames_for_agent(subj, relation="HAS_BRANCHES")
            if not frames:
                frames = [
                    f for f in self.hypergraph.get_frames_for_agent(subj)
                    if attr_word in f.get("patient", "").lower() or attr_word in f.get("raw_text", "").lower()
                ]
            if not frames:
                frames = [
                    f for f in self.hypergraph.frames.values()
                    if f"branch of {subj}" in f.get("patient", "").lower()
                    or f"branches of {subj}" in f.get("raw_text", "").lower()
                ]
            if frames:
                return self._summarize_entity_frames(full_text, subj, frames[:6], intent="query_parts")
            return self._reply(
                full_text, realizer.realize_unknown(qtype, subj),
                intent="query_parts", mode="unknown", confidence=0.0,
                proof_steps=[f"No HAS_PART or HAS_BRANCHES frames found for '{subj}'."],
            )

        # 13. EXAMPLES / INSTANCES
        if qtype == "QUERY_EXAMPLES":
            res = self.hypergraph.query_examples(pq.subject)
            if res["mode"] != "unknown":
                self.active_topic = self.hypergraph.resolve_alias(pq.subject)
            return self._reply(
                full_text,
                realizer.realize_examples(pq.subject, res),
                intent="query_examples",
                mode=res["mode"],
                confidence=res["confidence"],
                recalled_ids=res["used_frame_ids"],
                proof_steps=res["proof_steps"],
            )

        # 3. ALIAS / SYNONYM
        if qtype == "QUERY_ALIAS":
            subj = normalize_entity(pq.subject)
            aka_frames = self.hypergraph.get_frames_for_agent(subj, relation="ALSO_KNOWN_AS")
            if not aka_frames:
                aka_frames = self.hypergraph.get_frames_for_patient(subj, relation="ALSO_KNOWN_AS")
            if aka_frames:
                return self._summarize_entity_frames(full_text, subj, aka_frames, intent="query_alias")
            return self._reply(
                full_text, realizer.realize_unknown(qtype, subj),
                intent="query_alias", mode="unknown", confidence=0.0,
                proof_steps=[f"No ALSO_KNOWN_AS alias stored for '{subj}'."],
            )

        # 5. CAPABILITY (CAN / CANNOT) — Strict boundary enforcement
        if qtype == "QUERY_CAN":
            subj = self.hypergraph.resolve_alias(pq.subject)
            ability = pq.target
            disp_subj = realizer.display_entity(subj)
            res = self.hypergraph.query_capability_or_relation(subj, "CAN", ability)
            if res["mode"] == "contradicted":
                msg = (
                    f"My memory holds conflicting evidence on whether {disp_subj} can {ability}. "
                    "Tell me which one is correct to resolve it."
                )
                return self._reply(
                    full_text, msg, intent="query_can", mode="contradicted",
                    confidence=res["confidence"], recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            if res["mode"] in {"stored", "derived"}:
                self.active_topic = subj
                pol = res["polarity"]
                pct = round(res["confidence"] * 100)
                basis = "directly stored" if res["mode"] == "stored" else "derived via inheritance"
                ans = (
                    f"Yes, {disp_subj} can {ability} ({basis}, confidence {pct}%)."
                    if pol > 0
                    else f"No, {disp_subj} cannot {ability} ({basis}, confidence {pct}%)."
                )
                return self._reply(
                    full_text, ans, intent="query_can", mode=res["mode"],
                    confidence=res["confidence"], recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            proofs = [f"Boundary check: no stored or inherited CAN frame links '{subj}' to '{ability}'."]
            note = ""
            alt_hits = self.hypergraph.semantic_search(ability, top_k=3, min_score=0.35)
            for alt_fr, alt_sc in alt_hits:
                if alt_fr.get("relation") == "CAN" and alt_fr.get("polarity", 1) > 0 and alt_fr.get("agent") != subj:
                    note = f" However, my memory shows that {realizer.frame_to_sentence(alt_fr)}"
                    proofs.append(f"Contrast note ({alt_sc:.2f}): {alt_fr['agent']} CAN {alt_fr['patient']}")
                    break
            return self._reply(
                full_text,
                f"I have no stored evidence that {disp_subj} can {ability}.{note}",
                intent="query_can", mode="unknown",
                confidence=0.0, recalled_ids=[], proof_steps=proofs,
            )

        # 4. POLAR VERIFICATION (YES / NO)
        if qtype == "QUERY_VERIFY":
            subj = self.hypergraph.resolve_alias(pq.subject)
            res = self.hypergraph.query_verify(subj, pq.relation or "IS_A", pq.target)
            if res["mode"] != "unknown":
                self.active_topic = subj
            return self._reply(
                full_text,
                realizer.realize_verify(res, subj, pq.target),
                intent="query_verify",
                mode=res["mode"],
                confidence=res["confidence"],
                recalled_ids=res["used_frame_ids"],
                proof_steps=res["proof_steps"],
            )

        # 14. ROLE / EVENT (WHO / WHAT DID)
        if qtype == "QUERY_ROLE":
            role_ask = pq.meta.get("role_ask", "agent")
            verb = pq.action
            if role_ask == "agent" and pq.target:
                tgt = self.hypergraph.resolve_alias(pq.target)
                pat_frames = self.hypergraph.get_frames_for_patient(tgt)
                matches = [
                    f for f in pat_frames
                    if canon_verb(f.get("action", "")) == verb
                    or (verb in _CREATOR_VERBS and f.get("relation") == "CREATED")
                ]
                if matches:
                    top = matches[0]
                    self.active_topic = top["agent"]
                    conf = self.hypergraph.bayesian_confidence(top)
                    return self._reply(
                        full_text, realizer.frame_to_sentence(top),
                        intent="query_role_agent", mode="stored",
                        confidence=conf, recalled_ids=[top["id"]],
                        proof_steps=[f"Role-bound match: Agent={top['agent']}, Action={top['action']}, Patient={top['patient']}"],
                    )
            elif role_ask == "patient" and pq.subject:
                subj = self.hypergraph.resolve_alias(pq.subject)
                ag_frames = self.hypergraph.get_frames_for_agent(subj)
                matches = [
                    f for f in ag_frames
                    if canon_verb(f.get("action", "")) == verb
                    or (verb in _CREATOR_VERBS and f.get("relation") == "CREATED")
                ]
                if matches:
                    top = matches[0]
                    self.active_topic = subj
                    conf = self.hypergraph.bayesian_confidence(top)
                    return self._reply(
                        full_text, realizer.frame_to_sentence(top),
                        intent="query_role_patient", mode="stored",
                        confidence=conf, recalled_ids=[top["id"]],
                        proof_steps=[f"Role-bound match: Agent={top['agent']}, Action={top['action']}, Patient={top['patient']}"],
                    )

        # 15. QUANTITATIVE / SPATIAL / TEMPORAL
        if qtype == "QUERY_FACT_META":
            subtype = pq.meta.get("subtype", "count")
            subj = self.hypergraph.resolve_alias(pq.subject)
            rel_map = {"age": "HAS_AGE", "location": "LOCATED_IN", "count": "HAS_COUNT", "time": "CREATED_AT"}
            rel = rel_map.get(subtype, "HAS_COUNT")
            res = self.hypergraph.query_capability_or_relation(subj, rel)
            if res["mode"] in {"stored", "derived"} and res["frames"]:
                self.active_topic = subj
                return self._reply(
                    full_text,
                    realizer.realize_frames(res["frames"], max_items=2),
                    intent=f"query_{subtype}",
                    mode=res["mode"],
                    confidence=res["confidence"],
                    recalled_ids=res["used_frame_ids"],
                    proof_steps=res["proof_steps"],
                )
            if subtype == "count":
                tgt_word = (pq.target or "").lower()
                candidates = self.hypergraph.get_frames_for_agent(subj)
                if not candidates and tgt_word:
                    candidates = [
                        f for f in self.hypergraph.frames.values()
                        if tgt_word in f.get("patient", "").lower() and re.search(r"\d+", f.get("patient", ""))
                    ]
                num_matches = [
                    f for f in candidates
                    if re.search(r"\d+", f.get("patient", ""))
                    and (not tgt_word or tgt_word in f.get("patient", "").lower())
                ]
                if num_matches:
                    return self._summarize_entity_frames(full_text, num_matches[0]["agent"], num_matches[:2], intent="query_count")

        # 2. CLASSIFICATION / TYPE
        if qtype == "QUERY_CLASS":
            subj = self.hypergraph.resolve_alias(pq.subject)
            isa = self.hypergraph.get_frames_for_agent(subj, relation="IS_A")
            if isa:
                return self._summarize_entity_frames(full_text, subj, isa, intent="query_class")
            all_f = self.hypergraph.get_frames_for_agent(subj)
            if all_f:
                return self._summarize_entity_frames(full_text, subj, all_f, intent="query_class")
            return self._reply(
                full_text, realizer.realize_unknown(qtype, subj),
                intent="query_class", mode="unknown", confidence=0.0,
            )

        # 1. DEFINITION / MEANING
        if qtype == "QUERY_DEFINE":
            topic = self.hypergraph.resolve_alias(pq.subject)
            frames = self.hypergraph.get_frames_for_agent(topic)
            if frames:
                return self._summarize_entity_frames(full_text, topic, frames)
            rev_frames = self.hypergraph.get_frames_for_patient(topic)
            if rev_frames:
                return self._summarize_entity_frames(full_text, topic, rev_frames)
            if topic and len(topic) >= 3:
                partial_matches = [
                    ent for ent in self.hypergraph._by_agent.keys()
                    if re.search(r"\b" + re.escape(topic) + r"\b", ent)
                ]
                if partial_matches:
                    partial_matches.sort(key=len)
                    collected = []
                    for ent in partial_matches[:2]:
                        collected.extend(self.hypergraph.get_frames_for_agent(ent)[:2])
                    if collected:
                        return self._summarize_entity_frames(full_text, partial_matches[0], collected)

        return None

    def _semantic_and_episodic_fallback(self, query: str) -> Optional[Dict[str, Any]]:
        """Vector recall with strict lexical-overlap guard + episodic recall."""
        cleaned_q = self.parser.strip_wrappers(query).rstrip("?!. ")
        if cleaned_q and len(cleaned_q.split()) <= 3:
            topic = self.hypergraph.resolve_alias(cleaned_q)
            frames = self.hypergraph.get_frames_for_agent(topic)
            if frames:
                return self._summarize_entity_frames(query, topic, frames)

        q_tokens = set(tokenize_content(cleaned_q))
        sem_hits = self.hypergraph.semantic_search(cleaned_q, top_k=5, min_score=0.32)
        filtered_hits = []
        for fr, sc in sem_hits:
            if not is_valid_agent(fr.get("agent", ""), allow_clause=(fr.get("relation") == "IF_THEN")):
                continue
            f_blob = f"{fr.get('agent', '')} {fr.get('patient', '')} {fr.get('raw_text', '')}"
            f_tokens = set(tokenize_content(f_blob))
            overlap = q_tokens.intersection(f_tokens)
            if overlap or sc >= 0.48:
                filtered_hits.append((fr, sc))

        if filtered_hits:
            top_frames = [fr for fr, _ in filtered_hits[:3]]
            top_score = filtered_hits[0][1]
            self.active_topic = top_frames[0]["agent"]
            snippets = realizer.realize_frames(top_frames, max_items=3)
            fids = [fr["id"] for fr in top_frames]
            proofs = [
                f"Vector recall ({sc:.2f}): {fr['agent']} {fr['relation']} {fr['patient']}"
                for fr, sc in filtered_hits[:3]
            ]
            return self._reply(
                query,
                snippets,
                intent="semantic_recall",
                mode="stored",
                confidence=min(0.95, max(0.45, top_score)),
                recalled_ids=fids,
                proof_steps=proofs,
            )

        ep_hits = self.episodic.recall_similar(cleaned_q, top_k=2, min_score=0.42)
        if ep_hits:
            best_ep, ep_score = ep_hits[0]
            ep_fids = best_ep.get("recalled_frame_ids") or []
            frames_still_active = (not ep_fids) or any(fid in self.hypergraph.frames for fid in ep_fids)
            if frames_still_active and best_ep.get("response") and best_ep.get("mode") != "unknown":
                ep_tokens = set(tokenize_content(best_ep.get("user_input", "")))
                if q_tokens.intersection(ep_tokens):
                    return self._reply(
                        query,
                        "From a similar earlier episode: " + best_ep["response"],
                        intent="episodic_recall",
                        mode="derived",
                        confidence=round(ep_score * 0.85, 3),
                        recalled_ids=best_ep.get("recalled_frame_ids", []),
                        proof_steps=[f"Matched prior episode {best_ep['id']} (sim={ep_score:.2f})."],
                    )
        return None

    def observe_bulk(
        self,
        text: str,
        llm_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main cognitive turn entrypoint for NSM VB v1.5."""
        cleaned = (text or "").strip()
        if not cleaned:
            return self._reply("", "Please type a message so I can think or learn.", "empty", "unknown", 0.0, record_episode=False)

        low = cleaned.lower().strip(" .!?")

        if low in _GREETINGS:
            user_name = self.profile.get("name")
            greet = f"Hello{', ' + user_name if user_name else ''}! NSM VB v1.5 is online. Teach me anything or ask a question in natural English."
            return self._reply(cleaned, greet, "greeting", "stored", 1.0, record_episode=False)

        meta_res = self._handle_meta_recall(cleaned)
        if meta_res:
            return meta_res

        fb_res = self._handle_feedback_text(cleaned)
        if fb_res:
            return fb_res

        forget_res = self._handle_forget(cleaned)
        if forget_res:
            return forget_res

        prof_res = self._handle_profile(cleaned)
        if prof_res:
            return prof_res

        self_res = self._handle_self_query(cleaned)
        if self_res:
            return self._maybe_enhance_with_cortex(cleaned, self_res, llm_url, llm_model, llm_key)

        # Split input at full stops and compound comma clauses while preserving lists & If-clauses
        raw_units = [s.strip() for s in re.split(r"(?<=[.!?;\n])\s+|\n+", cleaned) if s.strip()]
        sentence_units: List[str] = []
        for ru in raw_units:
            sentence_units.extend(self.parser.split_comma_clauses(ru))

        # MULTI-SENTENCE MODE (2+ sentences): filter each sentence one by one against memory
        if len(sentence_units) >= 2:
            learned_frames: List[Dict[str, Any]] = []
            learned_summaries: List[str] = []
            rejected_notes: List[str] = []
            collected_answers: List[str] = []
            seen_answers = set()
            collected_fids: List[str] = []
            collected_proofs: List[str] = []
            confs: List[float] = []
            any_stored = False

            for idx, sent in enumerate(sentence_units, 1):
                stripped_s = self.parser.strip_wrappers(sent)
                first_tok = stripped_s.split()[0].lower() if stripped_s else ""
                is_explicit_q = sent.endswith("?") or (first_tok in {
                    "who", "what", "where", "when", "why", "how", "which",
                    "can", "could", "does", "do", "did", "is", "are", "was", "were",
                })

                # 1) Check declarative teaching statement first if not an explicit question
                if not is_explicit_q:
                    ps = self.parser.parse_statement(sent, last_subject=self.active_topic)
                    if ps:
                        try:
                            fr = self.hypergraph.add_frame(
                                relation=ps.relation,
                                agent=ps.agent,
                                patient=ps.patient,
                                action=ps.action,
                                modifier=ps.modifier,
                                polarity=ps.polarity,
                                source="user",
                                raw_text=ps.raw_text,
                            )
                            learned_frames.append(fr)
                            learned_summaries.append(realizer.frame_to_sentence(fr))
                            if ps.relation != "IF_THEN" and fr["agent"] not in {"we", "you", "i", "they", "them", "he", "she", "it", "this", "that"}:
                                self.active_topic = fr["agent"]
                            continue
                        except ValueError as ve:
                            rejected_notes.append(str(ve))
                            continue

                # 2) Otherwise filter this sentence against enabled workflows, structured questions, and sentence-token matcher
                wf_s = skill_engine.match_skill_workflow(self, sent)
                if wf_s:
                    ans = wf_s["response"]
                    if ans not in seen_answers:
                        seen_answers.add(ans)
                        collected_answers.append(ans)
                    confs.append(wf_s["confidence"])
                    any_stored = True
                    collected_proofs.append(f"Sentence {idx} workflow match: {wf_s['proof_steps'][0]}")
                    continue

                pq = self.parser.parse_question(sent, active_topic=self.active_topic)
                if pq:
                    if pq.subject and pq.subject not in {"it", "its", "this", "that", "they", "them"}:
                        self.active_topic = pq.subject
                    q_res = self._dispatch_question(pq, sent)
                    if q_res and q_res.get("mode") in {"stored", "derived", "contradicted"}:
                        ans = q_res["response"]
                        if ans not in seen_answers:
                            seen_answers.add(ans)
                            collected_answers.append(ans)
                        for fid in q_res.get("recalled_frame_ids", []):
                            if fid not in collected_fids:
                                collected_fids.append(fid)
                        confs.append(q_res.get("confidence", 0.8))
                        if q_res.get("mode") == "stored":
                            any_stored = True
                        collected_proofs.append(f"Sentence {idx} structured match: {ans}")
                        continue

                # 3) Sentence-token percentage match (20% reference / 40%+ direct sentence lift)
                stm = self.hypergraph.sentence_token_match(sent)
                if stm["mode"] in {"stored", "derived"}:
                    ans = stm["sentence"]
                    if ans not in seen_answers:
                        seen_answers.add(ans)
                        collected_answers.append(ans)
                    for fid in stm["used_frame_ids"]:
                        if fid not in collected_fids:
                            collected_fids.append(fid)
                    confs.append(stm["confidence"])
                    if stm["mode"] == "stored":
                        any_stored = True
                    collected_proofs.append(f"Sentence {idx}: {stm['proof_steps'][0]}")
                else:
                    collected_proofs.append(f"Sentence {idx}: no reference >= 20% found.")

            # Pure teaching turn (all sentences were statements)
            if learned_frames and not collected_answers:
                fids = [f["id"] for f in learned_frames]
                proofs = [f"Stored role-bound frame: {f['agent']} {f['relation']} {f['patient']} (pol={f['polarity']})" for f in learned_frames]
                reply_text = (
                    f"Learned and bound in memory: {learned_summaries[0]}"
                    if len(learned_summaries) == 1
                    else f"Learned {len(learned_summaries)} structured facts: " + " ".join(learned_summaries[:4])
                )
                res = self._reply(
                    cleaned, reply_text, intent="teach", mode="stored",
                    confidence=0.95, recalled_ids=fids, proof_steps=proofs,
                    learned=learned_summaries,
                )
                return self._maybe_enhance_with_cortex(cleaned, res, llm_url, llm_model, llm_key)

            # Combined or multi-sentence reference recall
            if collected_answers:
                body = " ".join(collected_answers)
                if learned_summaries:
                    body = f"Learned {len(learned_summaries)} fact(s). " + body
                avg_conf = sum(confs) / len(confs) if confs else 0.75
                res = self._reply(
                    cleaned,
                    body,
                    intent="multi_sentence_recall",
                    mode="stored" if any_stored else "derived",
                    confidence=avg_conf,
                    recalled_ids=collected_fids + [f["id"] for f in learned_frames],
                    proof_steps=collected_proofs,
                    learned=learned_summaries,
                )
                return self._maybe_enhance_with_cortex(cleaned, res, llm_url, llm_model, llm_key)

            if rejected_notes:
                return self._reply(
                    cleaned,
                    f"I skipped that because: {rejected_notes[0]}",
                    intent="reject", mode="unknown", confidence=0.9,
                    proof_steps=rejected_notes,
                )

        # SINGLE-SENTENCE MODE
        wf_hit = skill_engine.match_skill_workflow(self, cleaned)
        if wf_hit:
            wf_res = self._reply(
                cleaned,
                wf_hit["response"],
                intent="skill_workflow",
                mode="stored",
                confidence=wf_hit["confidence"],
                proof_steps=wf_hit["proof_steps"],
            )
            return self._maybe_enhance_with_cortex(cleaned, wf_res, llm_url, llm_model, llm_key)

        parsed = self.parser.parse_turn(cleaned, active_topic=self.active_topic)
        learned_frames = []
        learned_summaries = []
        rejected_notes = []

        for st in parsed.statements:
            try:
                fr = self.hypergraph.add_frame(
                    relation=st.relation,
                    agent=st.agent,
                    patient=st.patient,
                    action=st.action,
                    modifier=st.modifier,
                    polarity=st.polarity,
                    source="user",
                    raw_text=st.raw_text,
                )
                learned_frames.append(fr)
                learned_summaries.append(realizer.frame_to_sentence(fr))
                if st.relation != "IF_THEN" and fr["agent"] not in {"we", "you", "i", "they", "them", "he", "she", "it", "this", "that"}:
                    self.active_topic = fr["agent"]
            except ValueError as ve:
                rejected_notes.append(str(ve))

        if parsed.questions:
            primary_q = parsed.questions[-1]
            q_res = self._dispatch_question(primary_q, cleaned)
            if q_res is not None and q_res.get("mode") in {"stored", "derived", "contradicted"}:
                if learned_summaries:
                    q_res["learned"] = learned_summaries
                    q_res["response"] = f"Learned {len(learned_summaries)} fact(s). " + q_res["response"]
                return self._maybe_enhance_with_cortex(cleaned, q_res, llm_url, llm_model, llm_key)

            # For open queries (non-strict-polar), try Sentence-Token Matcher (20% ref / 40%+ direct lift)
            if primary_q.qtype not in {"QUERY_CAN", "QUERY_VERIFY", "QUERY_CHOICE"}:
                stm = self.hypergraph.sentence_token_match(cleaned)
                if stm["mode"] in {"stored", "derived"}:
                    if stm["frames"]:
                        self.active_topic = stm["frames"][0]["agent"]
                    stm_res = self._reply(
                        cleaned,
                        stm["sentence"],
                        intent="sentence_token_recall",
                        mode=stm["mode"],
                        confidence=stm["confidence"],
                        recalled_ids=stm["used_frame_ids"],
                        proof_steps=stm["proof_steps"],
                    )
                    return self._maybe_enhance_with_cortex(cleaned, stm_res, llm_url, llm_model, llm_key)

            if q_res is None:
                q_res = self._semantic_and_episodic_fallback(cleaned)
            if q_res is None:
                q_res = self._reply(
                    cleaned,
                    realizer.realize_unknown(primary_q.qtype, primary_q.subject),
                    intent=primary_q.qtype.lower(),
                    mode="unknown",
                    confidence=0.0,
                    proof_steps=[f"No stored match for {primary_q.qtype} on '{primary_q.subject}'."],
                )
            if learned_summaries:
                q_res["learned"] = learned_summaries
                q_res["response"] = f"Learned {len(learned_summaries)} fact(s). " + q_res["response"]
            return self._maybe_enhance_with_cortex(cleaned, q_res, llm_url, llm_model, llm_key)

        if learned_frames:
            fids = [f["id"] for f in learned_frames]
            proofs = [f"Stored role-bound frame: {f['agent']} {f['relation']} {f['patient']} (pol={f['polarity']})" for f in learned_frames]
            reply_text = f"Learned and bound in memory: {learned_summaries[0]}"
            res = self._reply(
                cleaned, reply_text, intent="teach", mode="stored",
                confidence=0.95, recalled_ids=fids, proof_steps=proofs,
                learned=learned_summaries,
            )
            return self._maybe_enhance_with_cortex(cleaned, res, llm_url, llm_model, llm_key)

        if rejected_notes:
            return self._reply(
                cleaned,
                f"I skipped that because: {rejected_notes[0]}",
                intent="reject", mode="unknown", confidence=0.9,
                proof_steps=rejected_notes,
            )

        # Single free-form sentence: score every word against stored memory sentences (20% / 40%+ rules)
        stm_free = self.hypergraph.sentence_token_match(cleaned)
        if stm_free["mode"] in {"stored", "derived"}:
            if stm_free["frames"]:
                self.active_topic = stm_free["frames"][0]["agent"]
            stm_res = self._reply(
                cleaned,
                stm_free["sentence"],
                intent="sentence_token_recall",
                mode=stm_free["mode"],
                confidence=stm_free["confidence"],
                recalled_ids=stm_free["used_frame_ids"],
                proof_steps=stm_free["proof_steps"],
            )
            return self._maybe_enhance_with_cortex(cleaned, stm_res, llm_url, llm_model, llm_key)

        sem_res = self._semantic_and_episodic_fallback(cleaned)
        if sem_res:
            return self._maybe_enhance_with_cortex(cleaned, sem_res, llm_url, llm_model, llm_key)

        if llm_url and llm_model:
            analysis = cortex_api.analyze_with_cortex(cleaned, llm_url, llm_model, llm_key)
            if analysis:
                if analysis.get("is_sarcastic") and analysis.get("sentiment") == "negative":
                    fb = self.apply_feedback(positive=False)
                    return self._reply(
                        cleaned,
                        f"Caught the sarcasm — {fb['message']} Let me know the correct detail.",
                        intent="feedback_negative", mode="stored", confidence=0.9,
                        proof_steps=["Cortex detected sarcastic negative feedback.", fb["message"]],
                        cortex_used=True, record_episode=False,
                    )
                api_facts = analysis.get("facts") or []
                api_learned: List[str] = []
                api_fids: List[str] = []
                for fc in api_facts[:5]:
                    if not isinstance(fc, dict):
                        continue
                    ag = clean_phrase(str(fc.get("agent", "")))
                    pat = clean_phrase(str(fc.get("patient", "")))
                    if ag and pat:
                        try:
                            fr = self.hypergraph.add_frame(
                                relation=str(fc.get("relation", "RELATED_TO")),
                                agent=ag, patient=pat,
                                action=str(fc.get("action", "")),
                                polarity=int(fc.get("polarity", 1)),
                                source="cortex", raw_text=cleaned,
                            )
                            api_fids.append(fr["id"])
                            api_learned.append(realizer.frame_to_sentence(fr))
                        except ValueError:
                            pass
                if api_learned:
                    base_ans = "Learned via Cortex parsing: " + " ".join(api_learned)
                    res = self._reply(
                        cleaned, base_ans, intent="teach", mode="stored",
                        confidence=0.88, recalled_ids=api_fids,
                        proof_steps=["Samu Lab Cortex extracted structured role-filler facts."],
                        learned=api_learned, cortex_used=True,
                    )
                    return self._maybe_enhance_with_cortex(cleaned, res, llm_url, llm_model, llm_key)

        unknown_res = self._reply(
            cleaned,
            realizer.realize_unknown(),
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
        recalled_ctx = []
        for fid in result.get("recalled_frame_ids", [])[:4]:
            fr = self.hypergraph.frames.get(fid)
            if fr:
                recalled_ctx.append(realizer.frame_to_sentence(fr))

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
            if self.episodic.episodes and self.episodic.episodes[-1].get("id") == result.get("episode_id"):
                self.episodic.episodes[-1]["response"] = polished[:500]
        return result

    def state(self) -> Dict[str, Any]:
        last_ep = self.episodic.get_last_episode(skip_meta=True)
        return {
            "version": self.version,
            "engine": f"NSM VB v{self.version} (NeuraSaMu)",
            "frames": len(self.hypergraph.frames),
            "senses": len(self.hypergraph.senses),
            "episodes": len(self.episodic.episodes),
            "schemas": len(self.episodic.schemas),
            "total_consolidated": self.episodic.total_consolidated_episodes,
            "turn_count": self.turn_count,
            "active_topic": self.active_topic,
            "installed_skills": len(self.skills.get("installed", {})),
            "custom_patterns": len(self.language_extensions.get("custom_patterns", [])),
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
            "package_type": "brain",
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turn_count": self.turn_count,
            "active_topic": self.active_topic,
            "profile": self.profile,
            "hypergraph": self.hypergraph.to_dict(),
            "episodic": self.episodic.to_dict(),
            "skills": self.skills,
            "language_extensions": self.language_extensions,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "Brain":
        brain = cls(seed_core=True)
        if not isinstance(data, dict):
            return brain

        if str(data.get("nsm_version", "")) in {"1.4", "1.5"} or "hypergraph" in data:
            brain.created_at = float(data.get("created_at", brain.created_at))
            brain.updated_at = float(data.get("updated_at", brain.updated_at))
            brain.turn_count = int(data.get("turn_count", 0))
            if data.get("active_topic"):
                brain.active_topic = str(data["active_topic"])
            if isinstance(data.get("profile"), dict):
                brain.profile.update(data["profile"])
            loaded_hg = TypedHypergraph.from_dict(data.get("hypergraph"))
            for sid, sdata in loaded_hg.senses.items():
                brain.hypergraph.senses[sid] = sdata
            for fid, fr in loaded_hg.frames.items():
                brain.hypergraph.frames[fid] = fr
                brain.hypergraph._index_frame_in_ram(fr)
            if isinstance(data.get("episodic"), dict):
                brain.episodic = EpisodicMemory.from_dict(data["episodic"])
            if isinstance(data.get("skills"), dict):
                if isinstance(data["skills"].get("installed"), dict):
                    brain.skills["installed"].update(data["skills"]["installed"])
                if isinstance(data["skills"].get("mcp_servers"), dict):
                    brain.skills["mcp_servers"].update(data["skills"]["mcp_servers"])
            if isinstance(data.get("language_extensions"), dict):
                pats = data["language_extensions"].get("custom_patterns", [])
                if isinstance(pats, list):
                    brain.language_extensions["custom_patterns"] = list(pats)
                    brain.parser.load_custom_patterns(pats)
            return brain

        brain._migrate_legacy(data)
        return brain

    def _migrate_legacy(self, data: Dict[str, Any]) -> None:
        """Import older NSM v1.x JSON brain exports cleanly into v1.5 hypergraph."""
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
