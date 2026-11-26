"""Data-driven English linguistic pattern matrix for NSM VB v1.5.

Separates linguistic rules from reasoning logic so:
1. Compositional wrappers multiply cleanly across all 16 question types & 14 relations.
2. Portable JSON pattern packs / skill packs can extend patterns without editing code.
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# 1. Conversational Wrappers & Fillers (stripped iteratively before parsing)
# ---------------------------------------------------------------------------

LEADING_FILLER_PATTERNS: List[str] = [
    r"^(?:(?:ok|okay|alright|hey|hi|hello|well|so|now|please|plz|bro|listen|actually|basically|hmm)\b[,:\s-]+)+",
]

# Indirect wrappers stripped ONLY when followed by an actual question/clause
INDIRECT_QUESTION_WRAPPERS: List[str] = [
    r"^(?:can|could|would)\s+you\s+(?:please\s+)?(?:tell\s+me|explain(?:\s+to\s+me)?)\s+(?:that\s+|if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did)\b|[a-zA-Z0-9])",
    r"^do\s+you\s+know\s+(?:that\s+|if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did)\b|[a-zA-Z0-9])",
    r"^i\s+(?:was\s+wondering|want\s+to\s+know|would\s+like\s+to\s+know)\s+(?:that\s+|if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did)\b|[a-zA-Z0-9])",
    r"^(?:please\s+)?tell\s+me\s+(?:if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did)\b)",
]

TRAILING_FILLER_PATTERNS: List[str] = [
    r"[,;\s]+(?:please|plz|bro)$",
]

REMEMBER_PREFIX_PATTERN: str = (
    r"^(?:remember(?:\s+this|\s+that)?|note(?:\s+this|\s+that)?|"
    r"learn(?:\s+this|\s+that)?|save(?:\s+this|\s+that)?)[,:\s-]+"
)

# ---------------------------------------------------------------------------
# 2. Lexical Helpers & Guards
# ---------------------------------------------------------------------------

PRONOUN_SUBJECTS = frozenset({
    "it", "its", "this", "that", "they", "them", "their",
})

QUESTION_STARTERS = frozenset({
    "who", "what", "where", "when", "why", "how", "which",
    "can", "could", "does", "do", "did", "is", "are", "was", "were",
})

BAD_AGENT_STARTS = frozenset({
    "it", "this", "that", "these", "those", "there", "here", "they", "them",
    "what", "who", "where", "when", "why", "how", "which", "remember", "ok", "okay",
    "if", "when", "while", "because", "although", "coming", "however",
})

VERB_LEMMA: Dict[str, str] = {
    "bit": "bite", "bites": "bite", "bitten": "bite",
    "ate": "eat", "eats": "eat", "eaten": "eat",
    "chased": "chase", "chases": "chase",
    "built": "build", "builds": "build",
    "created": "create", "creates": "create",
    "made": "make", "makes": "make",
    "founded": "found", "founds": "found",
    "developed": "develop", "develops": "develop",
    "invented": "invent", "invents": "invent",
    "designed": "design", "designs": "design",
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

# ---------------------------------------------------------------------------
# 3. Master Question Taxonomy (All 16 Core Types - Strict Priority Order)
# ---------------------------------------------------------------------------

QUESTION_RULES: List[Dict[str, Any]] = [
    # 16. FOLLOW-UP / ELABORATION
    {
        "id": "q_followup_en",
        "qtype": "QUERY_FOLLOWUP",
        "lang": "en",
        "pattern": r"^(?:tell\s+me\s+more|what\s+else|anything\s+else|more\s+details?|elaborate|go\s+on|continue|explain\s+(?:it\s+|that\s+)?(?:more|simply|in\s+simple\s+(?:words|terms)))$",
        "slots": {},
        "meta": {"style": "elaborate"},
    },

    # 12. COMPARISON / CONTRAST
    {
        "id": "q_compare_diff_en",
        "qtype": "QUERY_COMPARE",
        "lang": "en",
        "pattern": r"^(?:what(?:'s|\s+is|\s+are)\s+(?:the\s+)?)?(?:difference|differences)\s+between\s+(.+?)\s+and\s+(.+)$",
        "slots": {"subject": 1, "secondary_subject": 2},
        "meta": {},
    },
    {
        "id": "q_compare_verb_en",
        "qtype": "QUERY_COMPARE",
        "lang": "en",
        "pattern": r"^compare\s+(.+?)\s+(?:and|with|vs\.?|versus)\s+(.+)$",
        "slots": {"subject": 1, "secondary_subject": 2},
        "meta": {},
    },
    {
        "id": "q_compare_howdiff_en",
        "qtype": "QUERY_COMPARE",
        "lang": "en",
        "pattern": r"^how\s+(?:is|are|does)\s+(.+?)\s+different\s+from\s+(.+)$",
        "slots": {"subject": 1, "secondary_subject": 2},
        "meta": {},
    },
    {
        "id": "q_compare_vs",
        "qtype": "QUERY_COMPARE",
        "lang": "en",
        "pattern": r"^(.+?)\s+(?:vs\.?|versus)\s+(.+)$",
        "slots": {"subject": 1, "secondary_subject": 2},
        "meta": {},
    },

    # 6. CHOICE / ALTERNATIVE
    {
        "id": "q_choice_is_a_en",
        "qtype": "QUERY_CHOICE",
        "lang": "en",
        "pattern": r"^(?:is|are)\s+(.+?)\s+(?:a|an)\s+(.+?)\s+or\s+(?:a|an)?\s*(.+)$",
        "slots": {"subject": 1, "option_a": 2, "option_b": 3},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_choice_is_en",
        "qtype": "QUERY_CHOICE",
        "lang": "en",
        "pattern": r"^(?:is|are)\s+(.+?)\s+(.+?)\s+or\s+(?:a|an)?\s*(.+)$",
        "slots": {"subject": 1, "option_a": 2, "option_b": 3},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_choice_which_en",
        "qtype": "QUERY_CHOICE",
        "lang": "en",
        "pattern": r"^which\s+(?:one\s+)?(?:is\s+)?([a-zA-Z]+)[,:]?\s+(.+?)\s+or\s+(.+)$",
        "slots": {"target": 1, "option_a": 2, "option_b": 3},
        "meta": {"relation": "COMPARED_TO"},
    },

    # 8. CONSEQUENCE / HYPOTHETICAL
    {
        "id": "q_ifthen_en_1",
        "qtype": "QUERY_IF_THEN",
        "lang": "en",
        "pattern": r"^what\s+(?:happens|will\s+happen|would\s+happen)\s+(?:if|when)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "IF_THEN"},
    },
    {
        "id": "q_ifthen_en_2",
        "qtype": "QUERY_IF_THEN",
        "lang": "en",
        "pattern": r"^what\s+if\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "IF_THEN"},
    },
    {
        "id": "q_ifthen_en_3",
        "qtype": "QUERY_IF_THEN",
        "lang": "en",
        "pattern": r"^if\s+(.+?)[,]?\s+(?:then\s+)?what\s+(?:happens|will\s+happen|would\s+happen)$",
        "slots": {"subject": 1},
        "meta": {"relation": "IF_THEN"},
    },

    # 7. CAUSAL (WHY / REASON)
    {
        "id": "q_cause_what_en",
        "qtype": "QUERY_CAUSE",
        "lang": "en",
        "pattern": r"^what\s+causes?\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "CAUSES"},
    },
    {
        "id": "q_cause_reason_en",
        "qtype": "QUERY_CAUSE",
        "lang": "en",
        "pattern": r"^what\s+(?:is|are)\s+the\s+(?:cause|causes|reason|reasons)\s+(?:of|for)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "CAUSES"},
    },
    {
        "id": "q_cause_why_en",
        "qtype": "QUERY_CAUSE",
        "lang": "en",
        "pattern": r"^why\s+(?:does|do|did|is|are)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "CAUSES"},
    },

    # 10. PURPOSE / UTILITY
    {
        "id": "q_purpose_usedfor_en",
        "qtype": "QUERY_PURPOSE",
        "lang": "en",
        "pattern": r"^what\s+(?:is|are)\s+(.+?)\s+used\s+for$",
        "slots": {"subject": 1},
        "meta": {"relation": "USED_FOR"},
    },
    {
        "id": "q_purpose_of_en",
        "qtype": "QUERY_PURPOSE",
        "lang": "en",
        "pattern": r"^what\s+(?:is|are)\s+the\s+(?:use|uses|purpose|function|role)\s+of\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "USED_FOR"},
    },
    {
        "id": "q_purpose_do_en",
        "qtype": "QUERY_PURPOSE",
        "lang": "en",
        "pattern": r"^what\s+(?:does|do)\s+(.+?)\s+do$",
        "slots": {"subject": 1},
        "meta": {"relation": "USED_FOR"},
    },
    {
        "id": "q_purpose_need_en",
        "qtype": "QUERY_PURPOSE",
        "lang": "en",
        "pattern": r"^why\s+do\s+we\s+(?:use|need)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "USED_FOR"},
    },

    # 9. PROCEDURAL (HOW IT WORKS)
    {
        "id": "q_how_work_en",
        "qtype": "QUERY_HOW",
        "lang": "en",
        "pattern": r"^how\s+(?:does|do)\s+(.+?)\s+work$",
        "slots": {"subject": 1},
        "meta": {"relation": "WORKS_BY"},
    },
    {
        "id": "q_how_made_en",
        "qtype": "QUERY_HOW",
        "lang": "en",
        "pattern": r"^how\s+(?:is|are)\s+(.+?)\s+(?:made|built|created|formed|done)$",
        "slots": {"subject": 1},
        "meta": {"relation": "WORKS_BY"},
    },
    {
        "id": "q_how_to_en",
        "qtype": "QUERY_HOW",
        "lang": "en",
        "pattern": r"^how\s+(?:to|do\s+(?:you|we|i))\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "WORKS_BY"},
    },

    # 11. COMPOSITION / PARTS / BRANCHES
    {
        "id": "q_parts_madeof_en",
        "qtype": "QUERY_PARTS",
        "lang": "en",
        "pattern": r"^what\s+(?:is|are)\s+(.+?)\s+(?:made\s+of|composed\s+of|built\s+from)$",
        "slots": {"subject": 1},
        "meta": {"relation": "HAS_PART"},
    },
    {
        "id": "q_parts_list_en",
        "qtype": "QUERY_PARTS",
        "lang": "en",
        "pattern": r"^(?:what\s+(?:are|is)|list|name)\s+(?:the\s+)?(parts|components|branches|types|kinds|elements|layers|modules|fields|categories)\s+of\s+(.+)$",
        "slots": {"target": 1, "subject": 2},
        "meta": {"relation": "HAS_PART"},
    },
    {
        "id": "q_parts_its_en",
        "qtype": "QUERY_PARTS",
        "lang": "en",
        "pattern": r"^what\s+(?:are|is)\s+(its|their)\s+(parts|components|branches|types|elements)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "HAS_PART"},
    },

    # 13. EXAMPLES / INSTANCES
    {
        "id": "q_examples_en_1",
        "qtype": "QUERY_EXAMPLES",
        "lang": "en",
        "pattern": r"^(?:give(?:\s+me)?|list|name|show(?:\s+me)?)\s+(?:some\s+|an?\s+)?examples?\s+of\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_examples_en_2",
        "qtype": "QUERY_EXAMPLES",
        "lang": "en",
        "pattern": r"^what\s+are\s+(?:some\s+)?examples?\s+of\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "IS_A"},
    },

    # 3. ALIAS / SYNONYM
    {
        "id": "q_alias_en_1",
        "qtype": "QUERY_ALIAS",
        "lang": "en",
        "pattern": r"^what\s+else\s+(?:is|are)\s+(.+?)\s+(?:called|known\s+as)$",
        "slots": {"subject": 1},
        "meta": {"relation": "ALSO_KNOWN_AS"},
    },
    {
        "id": "q_alias_en_2",
        "qtype": "QUERY_ALIAS",
        "lang": "en",
        "pattern": r"^(?:what\s+is\s+)?(?:another|other)\s+names?\s+for\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "ALSO_KNOWN_AS"},
    },

    # 5. CAPABILITY (CAN / CANNOT)
    {
        "id": "q_can_en",
        "qtype": "QUERY_CAN",
        "lang": "en",
        "pattern": r"^can\s+(.+?)\s+([a-zA-Z][a-zA-Z0-9 '-]*)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "CAN"},
    },
    {
        "id": "q_can_able_en",
        "qtype": "QUERY_CAN",
        "lang": "en",
        "pattern": r"^(?:is|are)\s+(.+?)\s+able\s+to\s+(.+)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "CAN"},
    },

    # 2. CLASSIFICATION / TYPE
    {
        "id": "q_class_en",
        "qtype": "QUERY_CLASS",
        "lang": "en",
        "pattern": r"^what\s+(?:kind|type|sort|category)\s+of\s+(?:.+?\s+)?(?:is|are)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "IS_A"},
    },

    # 15. QUANTITATIVE / SPATIAL / TEMPORAL
    {
        "id": "q_meta_howmany_have_en",
        "qtype": "QUERY_FACT_META",
        "lang": "en",
        "pattern": r"^how\s+many\s+(.+?)\s+(?:does|do)\s+(.+?)\s+have$",
        "slots": {"target": 1, "subject": 2},
        "meta": {"subtype": "count", "relation": "HAS_COUNT"},
    },
    {
        "id": "q_meta_howmany_in_en",
        "qtype": "QUERY_FACT_META",
        "lang": "en",
        "pattern": r"^how\s+many\s+(.+?)\s+(?:are\s+)?in\s+(.+)$",
        "slots": {"target": 1, "subject": 2},
        "meta": {"subtype": "count", "relation": "HAS_COUNT"},
    },
    {
        "id": "q_meta_howmany_simple_en",
        "qtype": "QUERY_FACT_META",
        "lang": "en",
        "pattern": r"^how\s+many\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"subtype": "count", "relation": "HAS_COUNT"},
    },
    {
        "id": "q_meta_age_en",
        "qtype": "QUERY_FACT_META",
        "lang": "en",
        "pattern": r"^how\s+old\s+is\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"subtype": "age", "relation": "HAS_AGE"},
    },
    {
        "id": "q_meta_where_en",
        "qtype": "QUERY_FACT_META",
        "lang": "en",
        "pattern": r"^where\s+(?:is|are|does|do)\s+(.+?)(?:\s+live|\s+located|\s+found)?$",
        "slots": {"subject": 1},
        "meta": {"subtype": "location", "relation": "LOCATED_IN"},
    },
    {
        "id": "q_meta_when_en",
        "qtype": "QUERY_FACT_META",
        "lang": "en",
        "pattern": r"^when\s+(?:was|were|did)\s+(.+?)(?:\s+created|\s+made|\s+founded|\s+invented|\s+built)?$",
        "slots": {"subject": 1},
        "meta": {"subtype": "time", "relation": "CREATED_AT"},
    },

    # 14. ROLE / EVENT (WHO / WHAT DID)
    {
        "id": "q_role_patient_en",
        "qtype": "QUERY_ROLE",
        "lang": "en",
        "pattern": r"^(?:who|what)\s+(?:did|does)\s+(.+?)\s+([a-zA-Z]+)$",
        "slots": {"subject": 1, "action": 2},
        "meta": {"role_ask": "patient", "relation": "ACTION"},
    },
    {
        "id": "q_role_agent_en",
        "qtype": "QUERY_ROLE",
        "lang": "en",
        "pattern": r"^(?:who|what)\s+(?!(?:is|are|was|were|did|does|do|has|have|can|causes|cause|happens|else|kind|type|if)\b)([a-zA-Z]+)\s+(.+)$",
        "slots": {"action": 1, "target": 2},
        "meta": {"role_ask": "agent", "relation": "ACTION"},
    },

    # 4. POLAR VERIFICATION (YES / NO)
    {
        "id": "q_verify_isa_en",
        "qtype": "QUERY_VERIFY",
        "lang": "en",
        "pattern": r"^(?:is|are)\s+(.+?)\s+(?:a|an)\s+(.+)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_verify_has_en",
        "qtype": "QUERY_VERIFY",
        "lang": "en",
        "pattern": r"^(?:does|do)\s+(.+?)\s+have\s+(.+)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "HAS"},
    },
    {
        "id": "q_verify_attr_en",
        "qtype": "QUERY_VERIFY",
        "lang": "en",
        "pattern": r"^(?:is|are)\s+(.+?)\s+(.+)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "DEFINED_AS"},
    },

    # 1. DEFINITION / MEANING
    {
        "id": "q_define_mean_en",
        "qtype": "QUERY_DEFINE",
        "lang": "en",
        "pattern": r"^what\s+does\s+(.+?)\s+mean$",
        "slots": {"subject": 1},
        "meta": {"relation": "DEFINED_AS"},
    },
    {
        "id": "q_define_whatis_en",
        "qtype": "QUERY_DEFINE",
        "lang": "en",
        "pattern": r"^(?:what|who)\s+(?:is|are)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "DEFINED_AS"},
    },
    {
        "id": "q_define_imperative_en",
        "qtype": "QUERY_DEFINE",
        "lang": "en",
        "pattern": r"^(?:tell\s+me\s+about|explain|define|describe|meaning\s+of)\s+(.+)$",
        "slots": {"subject": 1},
        "meta": {"relation": "DEFINED_AS"},
    },
]

# ---------------------------------------------------------------------------
# 4. Master Declarative Statement Matrix (All 14 Typed Relations)
# ---------------------------------------------------------------------------

STATEMENT_RULES: List[Dict[str, Any]] = [
    # 1. IF_THEN (Condition -> Consequence)
    {
        "id": "s_ifthen_en",
        "relation": "IF_THEN",
        "polarity": 1,
        "pattern": r"^(?:if|when)\s+(.+?)[,]\s*(?:then\s+)?(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "if_then",
        "allow_clause_agent": True,
    },

    # 2. HAS_BRANCHES
    {
        "id": "s_branches_en",
        "relation": "HAS_BRANCHES",
        "polarity": 1,
        "pattern": r"(?:branches|types|kinds|fields|categories)\s+of\s+([a-zA-Z][a-zA-Z0-9 '-]{1,35}?)(?:[,;:\s]+(?:most\s+popular|main|major|key|common|such\s+as|include|including)?\s*(?:are|include|includes|:))\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has_branches",
    },

    # 3. CAUSES
    {
        "id": "s_causes_en",
        "relation": "CAUSES",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:causes|cause|caused|leads?\s+to|results?\s+in)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "cause",
    },

    # 4. WORKS_BY
    {
        "id": "s_worksby_en",
        "relation": "WORKS_BY",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:works?\s+by|operates?\s+by|functions?\s+by)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "works_by",
    },

    # 5. USED_FOR
    {
        "id": "s_usedfor_en",
        "relation": "USED_FOR",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is|are)\s+(?:used\s+for|used\s+to|designed\s+for|meant\s+for)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "used_for",
    },

    # 6. ALSO_KNOWN_AS
    {
        "id": "s_aka_en",
        "relation": "ALSO_KNOWN_AS",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is\s+)?(?:also\s+known\s+as|also\s+called|aka|a\.k\.a\.)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "also_known_as",
    },

    # 7. HAS_PART
    {
        "id": "s_haspart_en",
        "relation": "HAS_PART",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:consists?\s+of|is\s+made\s+of|are\s+made\s+of|is\s+composed\s+of|contains?)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has_part",
    },

    # 8. COMPARED_TO
    {
        "id": "s_compare_en",
        "relation": "COMPARED_TO",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is|are)\s+(faster|slower|bigger|smaller|better|worse|cheaper|stronger|lighter|heavier|safer|more\s+[a-z]+|less\s+[a-z]+)\s+than\s+(.+)$",
        "agent_g": 1,
        "modifier_g": 2,
        "patient_g": 3,
        "action": "compared_to",
    },

    # 9. CAN (Negative & Positive)
    {
        "id": "s_cannot_en",
        "relation": "CAN",
        "polarity": -1,
        "pattern": r"^(.+?)\s+(?:cannot|can't|can\s+not)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "can",
    },
    {
        "id": "s_can_en",
        "relation": "CAN",
        "polarity": 1,
        "pattern": r"^(.+?)\s+can\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "can",
    },

    # 10. HAS_AGE & HAS_COUNT
    {
        "id": "s_age_en",
        "relation": "HAS_AGE",
        "polarity": 1,
        "pattern": r"^(.+?)\s+is\s+(\d{1,3})\s+years?\s+old$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has_age",
    },
    {
        "id": "s_count_en",
        "relation": "HAS_COUNT",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:has|have)\s+(\d+(?:,\d+)*(?:\s+(?:million|billion|thousand))?\s+[a-zA-Z][a-zA-Z0-9 '-]*)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has_count",
    },

    # 11. CREATED
    {
        "id": "s_created_en",
        "relation": "CREATED",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(created|built|made|founded|developed|invented|designed)\s+(.+)$",
        "agent_g": 1,
        "action_g": 2,
        "patient_g": 3,
    },

    # 12. LOCATED_IN
    {
        "id": "s_located_en",
        "relation": "LOCATED_IN",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:lives?\s+in|is\s+located\s+in|located\s+in|stays?\s+in|is\s+found\s+in)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "located_in",
    },

    # 13. HAS
    {
        "id": "s_has_en",
        "relation": "HAS",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:has|have)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has",
    },

    # 14. IS_A / DEFINED_AS / ACTION
    {
        "id": "s_isnot_en",
        "relation": "IS_A",
        "polarity": -1,
        "pattern": r"^(.+?)\s+(?:is|are)\s+not\s+(?:a|an)?\s*(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "is",
    },
    {
        "id": "s_isa_en",
        "relation": "IS_A",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is|are)\s+(?:a|an)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "is",
        "promote_long_to_defined": True,
    },
    {
        "id": "s_defined_en",
        "relation": "DEFINED_AS",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is|are|means)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "is",
    },
    {
        "id": "s_action_svo_en",
        "relation": "ACTION",
        "polarity": 1,
        "pattern": r"^([a-zA-Z][a-zA-Z0-9 '-]{1,35}?)\s+(bit|bite|bites|ate|eats|chased|chases|killed|kills|helped|helps|loved|loves|hated|hates|liked|likes|hit|hits|saw|sees|taught|teaches|broke|fixed|wrote)\s+([a-zA-Z][a-zA-Z0-9 '-]{1,40})$",
        "agent_g": 1,
        "action_g": 2,
        "modifier_g": 2,
        "patient_g": 3,
    },
]
