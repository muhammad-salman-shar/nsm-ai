"""Compositional Neuro-Symbolic English Language Parser for NSM VB v1.5.

Zero external dependencies (stdlib only). Handles:
- Conversational wrapper & filler stripping
- All 16 core question types with clean slot extraction
- All 14 typed declarative statement relations (multi-sentence safe)
- Active-topic slot-level coreference ("it", "its", "this", "that")
- Runtime loading of portable JSON custom patterns (`language_extensions`)
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern, Tuple

from src import language_matrix as lm

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;\n])\s+|\n+")


def clean_phrase(text: str) -> str:
    s = re.sub(r"\s+", " ", (text or "").strip())
    s = s.strip(" .,!?;:\"'`")
    s = re.sub(r"^(?:a|an|the)\s+", "", s, flags=re.IGNORECASE)
    return s.strip()


def normalize_slot(text: str) -> str:
    return clean_phrase(text).lower()


def canon_verb(verb: str) -> str:
    v = normalize_slot(verb)
    if v in lm.VERB_LEMMA:
        return lm.VERB_LEMMA[v]
    if len(v) > 4 and v.endswith("ed"):
        return v[:-2]
    if len(v) > 3 and v.endswith("s") and not v.endswith("ss"):
        return v[:-1]
    return v


def detect_language(text: str) -> str:
    """NSM VB v1.5 is standardized on pure English."""
    return "english"


def is_valid_agent(agent: str, allow_clause: bool = False) -> bool:
    if not agent:
        return False
    words = agent.lower().split()
    if not words:
        return False
    if allow_clause:
        return 1 <= len(words) <= 14
    if len(words) > 6:
        return False
    if words[0] in lm.BAD_AGENT_STARTS:
        return False
    if any(w in lm.QUESTION_STARTERS for w in words):
        return False
    if any(ch in agent for ch in ("(", ")", ",")):
        return False
    return True


@dataclass
class ParsedQuestion:
    qtype: str
    rule_id: str
    raw_text: str
    cleaned_text: str
    subject: str = ""
    secondary_subject: str = ""
    target: str = ""
    action: str = ""
    options: List[str] = field(default_factory=list)
    relation: str = ""
    language: str = "english"
    coref_resolved: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedStatement:
    relation: str
    agent: str
    patient: str
    action: str = ""
    modifier: str = ""
    polarity: int = 1
    rule_id: str = ""
    raw_text: str = ""


@dataclass
class ParsedTurn:
    raw_text: str
    language: str
    questions: List[ParsedQuestion] = field(default_factory=list)
    statements: List[ParsedStatement] = field(default_factory=list)
    active_topic_out: Optional[str] = None

    @property
    def turn_type(self) -> str:
        if self.questions and self.statements:
            return "mixed"
        if self.questions:
            return "question"
        if self.statements:
            return "statement"
        return "unknown"


class CompositionalParser:
    """Compiled, extensible English parser for NSM VB v1.5."""

    def __init__(self, custom_patterns: Optional[List[Dict[str, Any]]] = None):
        self._lead_re: List[Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in lm.LEADING_FILLER_PATTERNS
        ]
        self._indirect_re: List[Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in lm.INDIRECT_QUESTION_WRAPPERS
        ]
        self._trail_re: List[Pattern[str]] = [
            re.compile(p, re.IGNORECASE) for p in lm.TRAILING_FILLER_PATTERNS
        ]
        self._remember_re: Pattern[str] = re.compile(lm.REMEMBER_PREFIX_PATTERN, re.IGNORECASE)

        self._question_rules: List[Tuple[Dict[str, Any], Pattern[str]]] = []
        self._statement_rules: List[Tuple[Dict[str, Any], Pattern[str]]] = []

        self._compile_default_rules()
        if custom_patterns:
            self.load_custom_patterns(custom_patterns)

    def _compile_default_rules(self) -> None:
        self._question_rules = [
            (rule, re.compile(rule["pattern"], re.IGNORECASE))
            for rule in lm.QUESTION_RULES
        ]
        self._statement_rules = [
            (rule, re.compile(rule["pattern"], re.IGNORECASE))
            for rule in lm.STATEMENT_RULES
        ]

    def load_custom_patterns(self, custom_patterns: List[Dict[str, Any]]) -> int:
        """Safely compile and prepend portable JSON custom rules (skill/pattern packs)."""
        loaded = 0
        for item in custom_patterns:
            if not isinstance(item, dict) or not item.get("pattern"):
                continue
            try:
                compiled = re.compile(str(item["pattern"]), re.IGNORECASE)
            except re.error:
                continue
            kind = str(item.get("kind", "")).lower()
            if kind == "question" and item.get("qtype"):
                self._question_rules.insert(0, (item, compiled))
                loaded += 1
            elif kind == "statement" and item.get("relation"):
                self._statement_rules.insert(0, (item, compiled))
                loaded += 1
        return loaded

    def strip_wrappers(self, text: str) -> str:
        s = re.sub(r"\s+", " ", (text or "").strip())
        for _ in range(4):
            prev = s
            for rx in self._lead_re:
                s = rx.sub("", s).strip()
            for rx in self._indirect_re:
                s = rx.sub("", s).strip()
            for rx in self._trail_re:
                s = rx.sub("", s).strip()
            if s == prev:
                break
        return s

    @staticmethod
    def _extract_group(match: re.Match, spec: Any) -> str:
        if isinstance(spec, tuple):
            for idx in spec:
                val = match.group(idx)
                if val:
                    return val
            return ""
        if isinstance(spec, int):
            return match.group(spec) or ""
        return ""

    @staticmethod
    def _resolve_coref(slot_value: str, active_topic: Optional[str]) -> Tuple[str, bool]:
        if not active_topic:
            return slot_value, False
        norm = normalize_slot(slot_value)
        if norm in lm.PRONOUN_SUBJECTS:
            return normalize_slot(active_topic), True
        return slot_value, False

    def parse_question(
        self,
        sentence: str,
        active_topic: Optional[str] = None,
    ) -> Optional[ParsedQuestion]:
        raw = (sentence or "").strip()
        if not raw:
            return None

        stripped = self.strip_wrappers(raw).rstrip("?!. ")
        if not stripped:
            return None

        for rule, rx in self._question_rules:
            m = rx.match(stripped)
            if not m:
                continue

            slots = rule.get("slots", {})
            subj_raw = self._extract_group(m, slots.get("subject")) if "subject" in slots else ""
            sec_raw = self._extract_group(m, slots.get("secondary_subject")) if "secondary_subject" in slots else ""
            tgt_raw = self._extract_group(m, slots.get("target")) if "target" in slots else ""
            act_raw = self._extract_group(m, slots.get("action")) if "action" in slots else ""

            options: List[str] = []
            if "option_a" in slots and "option_b" in slots:
                opt_a = normalize_slot(self._extract_group(m, slots["option_a"]))
                opt_b = normalize_slot(self._extract_group(m, slots["option_b"]))
                if opt_a:
                    options.append(opt_a)
                if opt_b:
                    options.append(opt_b)

            if rule["qtype"] == "QUERY_DEFINE" and subj_raw:
                subj_raw = re.split(
                    r"\s+(?:and|or)\s+(?:what|who|how|why|where)\b",
                    subj_raw,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0]

            subject = normalize_slot(subj_raw)
            secondary = normalize_slot(sec_raw)
            target = normalize_slot(tgt_raw)
            action = canon_verb(act_raw) if act_raw else ""

            coref_used = False
            if rule["qtype"] == "QUERY_FOLLOWUP" and not subject and active_topic:
                subject = normalize_slot(active_topic)
                coref_used = True
            elif subject:
                subject, coref_used = self._resolve_coref(subject, active_topic)

            if target and not coref_used:
                target, tgt_coref = self._resolve_coref(target, active_topic)
                coref_used = coref_used or tgt_coref

            meta = dict(rule.get("meta", {}))
            rel = str(meta.get("relation", ""))

            return ParsedQuestion(
                qtype=rule["qtype"],
                rule_id=rule["id"],
                raw_text=raw,
                cleaned_text=stripped,
                subject=subject,
                secondary_subject=secondary,
                target=target,
                action=action,
                options=options,
                relation=rel,
                language="english",
                coref_resolved=coref_used,
                meta=meta,
            )

        return None

    def parse_statement(
        self,
        sentence: str,
        last_subject: Optional[str] = None,
    ) -> Optional[ParsedStatement]:
        raw = (sentence or "").strip()
        if not raw or raw.endswith("?"):
            return None

        cleaned = self.strip_wrappers(raw)
        cleaned = self._remember_re.sub("", cleaned).strip().rstrip(".!")
        if not cleaned:
            return None

        first_tok = cleaned.split()[0].lower()
        if first_tok in lm.QUESTION_STARTERS:
            return None

        # Multi-sentence pronoun coreference
        if last_subject and is_valid_agent(last_subject):
            m_it = re.match(
                r"^(?:in\s+[a-zA-Z '-]+,\s*)?it\s+(is|are|can|cannot|can't|has|have|works\s+by|is\s+used\s+for)\s+(.+)$",
                cleaned,
                re.IGNORECASE,
            )
            if m_it:
                cleaned = f"{last_subject} {m_it.group(1)} {m_it.group(2)}"

        for rule, rx in self._statement_rules:
            m = rx.search(cleaned) if rule["id"] == "s_branches_en" else rx.match(cleaned)
            if not m:
                continue

            ag_raw = m.group(rule["agent_g"]) if "agent_g" in rule else ""
            pat_raw = m.group(rule["patient_g"]) if "patient_g" in rule else ""
            agent = normalize_slot(ag_raw)
            patient = normalize_slot(pat_raw)

            allow_clause = bool(rule.get("allow_clause_agent", False))
            if not is_valid_agent(agent, allow_clause=allow_clause) or not patient:
                continue

            rel = str(rule["relation"]).upper()
            if rule.get("promote_long_to_defined") and len(patient.split()) > 4:
                rel = "DEFINED_AS"

            action = rule.get("action", "")
            if "action_g" in rule:
                action = canon_verb(m.group(rule["action_g"]))

            modifier = ""
            if "modifier_g" in rule:
                modifier = normalize_slot(m.group(rule["modifier_g"]))

            return ParsedStatement(
                relation=rel,
                agent=agent,
                patient=patient,
                action=action,
                modifier=modifier,
                polarity=int(rule.get("polarity", 1)),
                rule_id=rule["id"],
                raw_text=raw,
            )

        return None

    def split_comma_clauses(self, sentence: str) -> List[str]:
        """Split compound comma-separated clauses while preserving lists (A, B, and C), If-clauses, and participle/relative clauses."""
        s = (sentence or "").strip()
        if not s or "," not in s:
            return [s] if s else []
        if re.match(r"^(?:if|when|unless|whenever|although|because|since|while)\b", s, re.IGNORECASE):
            return [s]
        pieces = [p.strip() for p in re.split(r",\s*(?:and\s+|but\s+|while\s+|whereas\s+)?", s) if p.strip()]
        if len(pieces) < 2:
            return [s]
        sub_starters = {
            "which", "that", "who", "whom", "whose", "where", "when", "while", "whereas",
            "although", "though", "because", "since", "unless", "until", "including",
            "such", "meaning", "making", "allowing", "explaining", "providing", "producing",
            "releasing", "containing", "consisting", "causing", "depending", "giving",
            "showing", "taking", "pumping", "separating", "combining", "orbiting",
            "stating", "describing", "representing", "using", "leading", "resulting",
        }
        for idx, piece in enumerate(pieces):
            words = piece.split()
            if len(words) < 3:
                return [s]
            first_w = words[0].lower().strip(".,;:!?")
            if idx > 0 and (first_w in sub_starters or (len(first_w) > 5 and first_w.endswith("ing"))):
                return [s]
            if self.parse_statement(piece) is None and self.parse_question(piece) is None:
                return [s]
        return pieces

    def parse_turn(
        self,
        text: str,
        active_topic: Optional[str] = None,
    ) -> ParsedTurn:
        raw = (text or "").strip()
        turn = ParsedTurn(raw_text=raw, language="english", active_topic_out=active_topic)
        if not raw:
            return turn

        raw_parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(raw) if p.strip()]
        parts: List[str] = []
        for rp_item in raw_parts:
            parts.extend(self.split_comma_clauses(rp_item))

        non_it_pronouns = frozenset({"we", "you", "i", "they", "them", "he", "she", "it", "this", "that"})
        running_topic = active_topic

        for part in parts:
            stripped = self.strip_wrappers(part)
            first_tok = stripped.split()[0].lower() if stripped else ""
            looks_like_q = (
                part.endswith("?")
                or (first_tok in lm.QUESTION_STARTERS)
                or bool(re.search(r"\b(?:vs\.?|versus)\b", stripped, re.IGNORECASE))
                or stripped.lower().rstrip("?!. ") in {
                    "tell me more", "what else", "anything else",
                    "more details", "elaborate", "explain simply",
                }
            )

            if looks_like_q:
                pq = self.parse_question(part, active_topic=running_topic)
                if pq:
                    turn.questions.append(pq)
                    if pq.subject and pq.subject not in lm.PRONOUN_SUBJECTS:
                        running_topic = pq.subject
                    continue

            ps = self.parse_statement(part, last_subject=running_topic)
            if ps:
                turn.statements.append(ps)
                if ps.relation != "IF_THEN" and is_valid_agent(ps.agent) and ps.agent.lower() not in non_it_pronouns:
                    running_topic = ps.agent
                continue

            pq_fallback = self.parse_question(part, active_topic=running_topic)
            if pq_fallback:
                turn.questions.append(pq_fallback)
                if pq_fallback.subject and pq_fallback.subject not in lm.PRONOUN_SUBJECTS:
                    running_topic = pq_fallback.subject

        turn.active_topic_out = running_topic
        return turn
