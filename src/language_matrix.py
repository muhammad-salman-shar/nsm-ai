"""Data-driven English + Hinglish linguistic pattern matrix for NSM VB v1.5.

Separates linguistic rules from reasoning logic so:
1. Compositional wrappers multiply cleanly across all 16 question types & 14 relations.
2. Future portable JSON pattern packs / skill packs can extend patterns without editing code.
"""

from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# 1. Conversational Wrappers & Fillers (stripped iteratively before parsing)
# ---------------------------------------------------------------------------

LEADING_FILLER_PATTERNS: List[str] = [
    r"^(?:(?:ok|okay|alright|hey|hi|hello|well|so|now|please|plz|bro|yaar|bhai|listen|actually|basically|hmm|acha|accha|waise|sun|suno|dekho|zara)\b[,:\s-]+)+",
]

# Indirect wrappers stripped ONLY when followed by an actual question/clause
INDIRECT_QUESTION_WRAPPERS: List[str] = [
    r"^(?:can|could|would)\s+you\s+(?:please\s+)?(?:tell\s+me|explain(?:\s+to\s+me)?)\s+(?:that\s+|if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did|kya|kyun|kyon|kaise|kahan|kab|kaun|kitne|kitna|agar)\b|[a-zA-Z0-9])",
    r"^do\s+you\s+know\s+(?:that\s+|if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did|kya|kyun|kyon|kaise|kahan|kab|kaun|kitne|kitna|agar)\b|[a-zA-Z0-9])",
    r"^i\s+(?:was\s+wondering|want\s+to\s+know|would\s+like\s+to\s+know)\s+(?:that\s+|if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did|kya|kyun|kyon|kaise|kahan|kab|kaun|kitne|kitna|agar)\b|[a-zA-Z0-9])",
    r"^(?:please\s+)?tell\s+me\s+(?:if\s+|whether\s+)?(?=(?:what|who|where|when|why|how|which|is|are|can|does|do|did)\b)",
    # Hinglish indirect wrappers
    r"^(?:kya\s+)?(?:tumhe|tujhe|aapko|tumko)\s+pata\s+hai(?:\s+ki)?\s+",
    r"^(?:mujhe\s+)?(?:ye|yeh)\s+(?:batao|bata\s+do|batana|bata\s+sakte\s+ho|samjhao|samjha\s+do)(?:\s+ki)?\s+",
    r"^(?:mujhe\s+)?(?:batao|bata\s+do|batana|samjhao|samjha\s+do)\s+ki\s+",
]

TRAILING_FILLER_PATTERNS: List[str] = [
    r"[,;\s]+(?:please|plz|bro|yaar|bhai)$",
]

REMEMBER_PREFIX_PATTERN: str = (
    r"^(?:remember(?:\s+this|\s+that)?|note(?:\s+this|\s+that)?|"
    r"learn(?:\s+this|\s+that)?|save(?:\s+this|\s+that)?|"
    r"yaad\s+rakh(?:na|o)?(?:\s+ki)?)[,:\s-]+"
)

# ---------------------------------------------------------------------------
# 2. Lexical Helpers & Guards
# ---------------------------------------------------------------------------

HINGLISH_MARKERS = frozenset({
    "kya", "kyun", "kyon", "kyu", "kaise", "kahan", "kab", "kaun", "konsa", "kaunsa",
    "kitne", "kitna", "hai", "hain", "hota", "hoti", "hote", "mein", "aur", "farq",
    "fark", "antar", "wajah", "vajah", "kaam", "sakta", "sakti", "sakte", "nahi",
    "nahin", "agar", "agr", "toh", "batao", "batana", "samjhao", "misaal", "misal",
    "hisse", "bana", "bani", "bane", "kisne", "iska", "iski", "iske", "uska", "uski",
    "uske", "ek", "cheez", "matlab", "naam", "doosra", "dusra", "yaar", "bhai",
    "asaan", "lafzon", "baare", "karke", "liye", "istemal", "rehta", "milta",
})

PRONOUN_SUBJECTS = frozenset({
    "it", "its", "this", "that", "they", "them", "their",
    "ye", "yeh", "woh", "wo", "iska", "iski", "iske", "uska", "uski", "uske",
    "ismein", "usmein", "ise", "use",
})

QUESTION_STARTERS = frozenset({
    "who", "what", "where", "when", "why", "how", "which",
    "can", "could", "does", "do", "did", "is", "are", "was", "were",
    "kya", "kyun", "kyon", "kaise", "kahan", "kab", "kaun", "kitne", "kitna", "agar",
})

BAD_AGENT_STARTS = frozenset({
    "it", "this", "that", "these", "those", "there", "here", "they", "them",
    "what", "who", "where", "when", "why", "how", "which", "remember", "ok", "okay",
    "if", "when", "while", "because", "although", "coming", "however", "kya", "agar",
})

VERB_LEMMA: Dict[str, str] = {
    # English irregular & common verbs
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
    # Hinglish action verbs
    "banaya": "create", "banayi": "create", "banaye": "create",
    "likha": "write", "likhi": "write",
    "kata": "bite", "kaata": "bite",
    "toda": "break", "toota": "break",
    "mara": "hit", "maara": "hit",
    "kiya": "do",
}

# ---------------------------------------------------------------------------
# 3. Master Question Taxonomy (All 16 Core Types - Strict Priority Order)
# Each rule: {"id", "qtype", "lang", "pattern", "slots", "meta"}
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
    {
        "id": "q_followup_hi",
        "qtype": "QUERY_FOLLOWUP",
        "lang": "hi",
        "pattern": r"^(?:aur\s+batao|aur\s+kya(?:\s+hai)?|aur\s+kuch|iske\s+baare\s+mein\s+aur(?:\s+batao)?|uske\s+baare\s+mein\s+aur(?:\s+batao)?|asaan\s+lafzon\s+mein(?:\s+batao|\s+samjhao)?|simple\s+mein(?:\s+batao|\s+samjhao)?|detail\s+mein(?:\s+batao|\s+samjhao)?)$",
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
        "id": "q_compare_hi",
        "qtype": "QUERY_COMPARE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+aur\s+(.+?)\s+(?:mein|me)\s+(?:kya\s+)?(?:farq|fark|antar|difference)\s*(?:hai|hota\s+hai)?$",
        "slots": {"subject": 1, "secondary_subject": 2},
        "meta": {},
    },
    {
        "id": "q_compare_vs",
        "qtype": "QUERY_COMPARE",
        "lang": "any",
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
    {
        "id": "q_choice_hi_ya_ek",
        "qtype": "QUERY_CHOICE",
        "lang": "hi",
        "pattern": r"^(?:kya\s+)?(.+?)\s+ek\s+(.+?)\s+hai\s+ya\s+(?:ek\s+)?(.+?)(?:\s+hai)?$",
        "slots": {"subject": 1, "option_a": 2, "option_b": 3},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_choice_hi_ya",
        "qtype": "QUERY_CHOICE",
        "lang": "hi",
        "pattern": r"^(?:kya\s+)?(.+?)\s+(.+?)\s+hai\s+ya\s+(?:ek\s+)?(.+?)(?:\s+hai)?$",
        "slots": {"subject": 1, "option_a": 2, "option_b": 3},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_choice_hi_kaun",
        "qtype": "QUERY_CHOICE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+aur\s+(.+?)\s+(?:mein|me)\s+se\s+(?:kaun|konsa|kaunsa)\s+(.+?)(?:\s+hai|\s+hota\s+hai)?$",
        "slots": {"option_a": 1, "option_b": 2, "target": 3},
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
    {
        "id": "q_ifthen_hi",
        "qtype": "QUERY_IF_THEN",
        "lang": "hi",
        "pattern": r"^(?:(?:agar|agr)\s+)?(.+?)\s+(?:toh|to)\s+kya\s+(?:hoga|hota\s+hai|ho\s+ga)$",
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
    {
        "id": "q_cause_hi_kyun",
        "qtype": "QUERY_CAUSE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+(?:kyun|kyon|kyu)\s+(?:hota|hoti|hote|hua|hai|hain)(?:\s+hai|\s+hain)?$",
        "slots": {"subject": 1},
        "meta": {"relation": "CAUSES"},
    },
    {
        "id": "q_cause_hi_wajah",
        "qtype": "QUERY_CAUSE",
        "lang": "hi",
        "pattern": r"^(?:(.+?)\s+(?:ki|ka)|(iska|iski|uska|uski))\s+(?:wajah|vajah|reason)\s+kya\s+(?:hai|hota\s+hai)$",
        "slots": {"subject": (1, 2)},
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
    {
        "id": "q_purpose_hi_kaam",
        "qtype": "QUERY_PURPOSE",
        "lang": "hi",
        "pattern": r"^(?:aur\s+)?(.+?)\s+(?:kis|kya)\s+kaam\s+(?:aata|aati|aate|ata|karta|karti)\s*(?:hai|hain)?$",
        "slots": {"subject": 1},
        "meta": {"relation": "USED_FOR"},
    },
    {
        "id": "q_purpose_hi_use",
        "qtype": "QUERY_PURPOSE",
        "lang": "hi",
        "pattern": r"^(?:aur\s+)?(?:(.+?)\s+(?:ka|ki|ke)|(iska|iski|iske|uska|uski|uske))\s+(?:use|kaam|purpose|fayda|faida)\s+kya\s+(?:hai|hota\s+hai)$",
        "slots": {"subject": (1, 2)},
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
    {
        "id": "q_how_hi",
        "qtype": "QUERY_HOW",
        "lang": "hi",
        "pattern": r"^(?:aur\s+)?(.+?)\s+kaise\s+(?:kaam\s+karta|kaam\s+karti|work\s+karta|chalta|banta|banaya\s+jata)\s*(?:hai|hain)?$",
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
    {
        "id": "q_parts_hi_cheez",
        "qtype": "QUERY_PARTS",
        "lang": "hi",
        "pattern": r"^(.+?)\s+(?:kis\s+cheez\s+se|kin\s+cheezon\s+se|kisse)\s+(?:bana|bani|bane)\s*(?:hota\s+hai|hoti\s+hai|hai|hain)?$",
        "slots": {"subject": 1},
        "meta": {"relation": "HAS_PART"},
    },
    {
        "id": "q_parts_hi_hisse",
        "qtype": "QUERY_PARTS",
        "lang": "hi",
        "pattern": r"^(?:(.+?)\s+(?:ke|ki|ka)|(iska|iski|iske|uska|uski|uske))\s+(?:kitne\s+)?(hisse|parts|branches|types|components)\s+(?:kya\s+|kaun\s+se\s+)?(?:hain|hai|hote\s+hain)$",
        "slots": {"subject": (1, 2), "target": 3},
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
    {
        "id": "q_examples_hi",
        "qtype": "QUERY_EXAMPLES",
        "lang": "hi",
        "pattern": r"^(?:(.+?)\s+(?:ki|ke|ka)|(iska|iski|iske|uska|uski|uske))\s+(?:kuch\s+)?(?:misaal|misal|example|examples)\s+(?:do|batao|dein|kya\s+hain|kya\s+hai)$",
        "slots": {"subject": (1, 2)},
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
    {
        "id": "q_alias_hi_naam",
        "qtype": "QUERY_ALIAS",
        "lang": "hi",
        "pattern": r"^(?:(.+?)\s+(?:ka|ki|ke)|(iska|iski|iske|uska|uski|uske))\s+(?:doosra|dusra|aur)\s+naam\s+kya\s+(?:hai|hota\s+hai)$",
        "slots": {"subject": (1, 2)},
        "meta": {"relation": "ALSO_KNOWN_AS"},
    },
    {
        "id": "q_alias_hi_kehte",
        "qtype": "QUERY_ALIAS",
        "lang": "hi",
        "pattern": r"^(.+?)\s+ko\s+aur\s+kya\s+(?:kehte|bolte|kaha\s+jata)\s*(?:hain|hai)?$",
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
    {
        "id": "q_can_hi",
        "qtype": "QUERY_CAN",
        "lang": "hi",
        "pattern": r"^(?:kya\s+)?(.+?)\s+(.+?)\s+(?:kar\s+)?sakt[aei]\s*(?:hai|hain)?$",
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
    {
        "id": "q_class_hi",
        "qtype": "QUERY_CLASS",
        "lang": "hi",
        "pattern": r"^(.+?)\s+(?:kis\s+(?:type|kind|tarah|category)\s+(?:ki|ka)\s+(?:cheez\s+)?|kya\s+cheez\s+)(?:hai|hota\s+hai|hoti\s+hai)$",
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
    {
        "id": "q_meta_hi_count",
        "qtype": "QUERY_FACT_META",
        "lang": "hi",
        "pattern": r"^(.+?)\s+(?:mein|me)\s+kitne\s+(.+?)\s*(?:hote\s+hain|hain|hai)?$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"subtype": "count", "relation": "HAS_COUNT"},
    },
    {
        "id": "q_meta_hi_where",
        "qtype": "QUERY_FACT_META",
        "lang": "hi",
        "pattern": r"^(.+?)\s+kahan\s+(?:hota|hoti|hote|milta|rehta|located|hai|hain)(?:\s+hai|\s+hain)?$",
        "slots": {"subject": 1},
        "meta": {"subtype": "location", "relation": "LOCATED_IN"},
    },
    {
        "id": "q_meta_hi_when",
        "qtype": "QUERY_FACT_META",
        "lang": "hi",
        "pattern": r"^(.+?)\s+kab\s+(?:bana|bani|banaya\s+gaya|hua|start\s+hua)(?:\s+tha|\s+thi|\s+hai)?$",
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
    {
        "id": "q_role_agent_hi",
        "qtype": "QUERY_ROLE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+kisne\s+(banaya|banayi|likha|toda|kata|kaata|mara|kiya|created|built|invented)(?:\s+tha|\s+thi|\s+hai)?$",
        "slots": {"target": 1, "action": 2},
        "meta": {"role_ask": "agent", "relation": "ACTION"},
    },
    {
        "id": "q_role_event_hi",
        "qtype": "QUERY_ROLE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+ne\s+(.+?)\s+ke\s+saath\s+kya\s+kiya$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"role_ask": "action", "relation": "ACTION"},
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
    {
        "id": "q_verify_hi_has",
        "qtype": "QUERY_VERIFY",
        "lang": "hi",
        "pattern": r"^kya\s+(.+?)\s+(?:mein|me)\s+(.+?)\s+(?:hota|hoti|hote|hai|hain)(?:\s+hai|\s+hain)?$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "HAS"},
    },
    {
        "id": "q_verify_hi_isa_ek",
        "qtype": "QUERY_VERIFY",
        "lang": "hi",
        "pattern": r"^kya\s+(.+?)\s+ek\s+(.+?)\s+(?:hai|hota\s+hai|hoti\s+hai|hote\s+hain)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "IS_A"},
    },
    {
        "id": "q_verify_hi_isa",
        "qtype": "QUERY_VERIFY",
        "lang": "hi",
        "pattern": r"^kya\s+(.+?)\s+(.+?)\s+(?:hai|hota\s+hai|hoti\s+hai|hote\s+hain)$",
        "slots": {"subject": 1, "target": 2},
        "meta": {"relation": "IS_A"},
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
    {
        "id": "q_define_hi_matlab",
        "qtype": "QUERY_DEFINE",
        "lang": "hi",
        "pattern": r"^(?:(.+?)\s+(?:ka|ki)|(iska|iski|uska|uski))\s+matlab\s*(?:kya\s+(?:hai|hota\s+hai)|hai|hota\s+hai|batao|bata\s+do|samjhao)?$",
        "slots": {"subject": (1, 2)},
        "meta": {"relation": "DEFINED_AS"},
    },
    {
        "id": "q_define_hi_kya",
        "qtype": "QUERY_DEFINE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+kya\s+(?:hai|hota\s+hai|hoti\s+hai|hote\s+hain|hain)$",
        "slots": {"subject": 1},
        "meta": {"relation": "DEFINED_AS"},
    },
    {
        "id": "q_define_hi_baare",
        "qtype": "QUERY_DEFINE",
        "lang": "hi",
        "pattern": r"^(.+?)\s+ke\s+baare\s+mein\s+(?:batao|bata\s+do|samjhao)$",
        "slots": {"subject": 1},
        "meta": {"relation": "DEFINED_AS"},
    },
]

# ---------------------------------------------------------------------------
# 4. Master Declarative Statement Matrix (All 14 Typed Relations)
# Strict priority order: specific relations before generic IS_A / DEFINED_AS.
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
    {
        "id": "s_ifthen_hi",
        "relation": "IF_THEN",
        "polarity": 1,
        "pattern": r"^(?:agar|agr)\s+(.+?)\s+(?:toh|to)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "if_then",
        "allow_clause_agent": True,
    },

    # 2. HAS_BRANCHES (Types / Branches / Fields)
    {
        "id": "s_branches_en",
        "relation": "HAS_BRANCHES",
        "polarity": 1,
        "pattern": r"(?:branches|types|kinds|fields|categories)\s+of\s+([a-zA-Z][a-zA-Z0-9 '-]{1,35}?)(?:[,;:\s]+(?:most\s+popular|main|major|key|common|such\s+as|include|including)?\s*(?:are|include|includes|:))\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has_branches",
    },
    {
        "id": "s_branches_hi",
        "relation": "HAS_BRANCHES",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:ke|ki)\s+(?:main\s+|popular\s+)?(?:branches|types|hisse)\s+(.+?)\s+(?:hain|hai|hote\s+hain)$",
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
    {
        "id": "s_causes_hi",
        "relation": "CAUSES",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:ki\s+wajah\s+se|se)\s+(.+?)\s+(?:hota\s+hai|hoti\s+hai|hote\s+hain|ho\s+jata\s+hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "cause",
    },

    # 4. WORKS_BY (Process / Mechanism)
    {
        "id": "s_worksby_en",
        "relation": "WORKS_BY",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:works?\s+by|operates?\s+by|functions?\s+by)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "works_by",
    },
    {
        "id": "s_worksby_hi",
        "relation": "WORKS_BY",
        "polarity": 1,
        "pattern": r"^([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(.+?)\s+karke\s+kaam\s+karta\s+hai$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "works_by",
    },

    # 5. USED_FOR (Purpose / Utility)
    {
        "id": "s_usedfor_en",
        "relation": "USED_FOR",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is|are)\s+(?:used\s+for|used\s+to|designed\s+for|meant\s+for)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "used_for",
    },
    {
        "id": "s_usedfor_hi",
        "relation": "USED_FOR",
        "polarity": 1,
        "pattern": r"^([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(.+?)\s+ke\s+(?:liye|kaam)\s+(?:use\s+hota\s+hai|aata\s+hai|aati\s+hai|istemal\s+hota\s+hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "used_for",
    },

    # 6. ALSO_KNOWN_AS (Alias / Synonym)
    {
        "id": "s_aka_en",
        "relation": "ALSO_KNOWN_AS",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:is\s+)?(?:also\s+known\s+as|also\s+called|aka|a\.k\.a\.)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "also_known_as",
    },
    {
        "id": "s_aka_hi",
        "relation": "ALSO_KNOWN_AS",
        "polarity": 1,
        "pattern": r"^(.+?)\s+ko\s+(.+?)\s+bhi\s+(?:kehte|kaha\s+jata|bolte)\s*(?:hain|hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "also_known_as",
    },

    # 7. HAS_PART (Composition)
    {
        "id": "s_haspart_en",
        "relation": "HAS_PART",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:consists?\s+of|is\s+made\s+of|are\s+made\s+of|is\s+composed\s+of|contains?)\s+(.+)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "has_part",
    },
    {
        "id": "s_haspart_hi",
        "relation": "HAS_PART",
        "polarity": 1,
        "pattern": r"^([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(.+?)\s+se\s+(?:bana|bani|bane)\s+(?:hota\s+hai|hoti\s+hai|hai|hain)$",
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
    {
        "id": "s_compare_hi",
        "relation": "COMPARED_TO",
        "polarity": 1,
        "pattern": r"^(.+?)[,]?\s+(.+?)\s+se\s+(zyada\s+[a-z]+|tez|fast|slow|bada|chota|behtar)\s+(?:hai|hota\s+hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "modifier_g": 3,
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
    {
        "id": "s_cannot_hi",
        "relation": "CAN",
        "polarity": -1,
        "pattern": r"^([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(.+?)\s+nahi(?:n)?\s+(?:kar\s+)?sakt[aei]\s*(?:hai|hain)?$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "can",
    },
    {
        "id": "s_can_hi",
        "relation": "CAN",
        "polarity": 1,
        "pattern": r"^([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(.+?)\s+(?:kar\s+)?sakt[aei]\s*(?:hai|hain)?$",
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
    {
        "id": "s_count_hi",
        "relation": "HAS_COUNT",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:mein|me)\s+(\d+\s+[a-zA-Z][a-zA-Z0-9 '-]*)\s+(?:hote\s+hain|hain|hai)$",
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
    {
        "id": "s_created_hi",
        "relation": "CREATED",
        "polarity": 1,
        "pattern": r"^(.+?)\s+ne\s+(.+?)\s+(banaya|banayi|likha|invent\s+kiya|create\s+kiya)(?:\s+tha|\s+thi|\s+hai)?$",
        "agent_g": 1,
        "patient_g": 2,
        "action_g": 3,
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
    {
        "id": "s_located_hi",
        "relation": "LOCATED_IN",
        "polarity": 1,
        "pattern": r"^([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(.+?)\s+(?:mein|me)\s+(?:rehta|rehti|milta|located)\s*(?:hai|hain)?$",
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
    {
        "id": "s_has_hi",
        "relation": "HAS",
        "polarity": 1,
        "pattern": r"^(.+?)\s+(?:ke\s+paas|mein|me)\s+(.+?)\s+(?:hota\s+hai|hoti\s+hai|hai|hain)$",
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
        "id": "s_isnot_hi_ek",
        "relation": "IS_A",
        "polarity": -1,
        "pattern": r"^(.+?)\s+ek\s+(.+?)\s+nahi(?:n)?\s+(?:hai|hota\s+hai|hoti\s+hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "is",
    },
    {
        "id": "s_isnot_hi",
        "relation": "IS_A",
        "polarity": -1,
        "pattern": r"^(.+?)\s+(.+?)\s+nahi(?:n)?\s+(?:hai|hota\s+hai|hoti\s+hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "is",
    },
    {
        "id": "s_isa_hi",
        "relation": "IS_A",
        "polarity": 1,
        "pattern": r"^(.+?)\s+ek\s+(.+?)\s+(?:hai|hota\s+hai|hoti\s+hai)$",
        "agent_g": 1,
        "patient_g": 2,
        "action": "is",
        "promote_long_to_defined": True,
    },
    {
        "id": "s_defined_hi",
        "relation": "DEFINED_AS",
        "polarity": 1,
        "pattern": r"^([a-zA-Z0-9_-]+)\s+(.+?)\s+(?:hota\s+hai|hoti\s+hai|hote\s+hain)$",
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
