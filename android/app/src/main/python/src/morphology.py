# L4: Centralized Morphology Engine (Data-Driven)

IRREGULAR_NOUNS = {
    "child": "children", "man": "men", "woman": "women",
    "person": "people", "mouse": "mice", "goose": "geese",
    "tooth": "teeth", "foot": "feet", "ox": "oxen"
}

IRREGULAR_VERBS_PAST = {
    "eat": "ate", "go": "went", "see": "saw", "run": "ran",
    "make": "made", "take": "took", "give": "gave", "know": "knew",
    "think": "thought", "feel": "felt", "find": "found", "drink": "drank",
    "write": "wrote", "swim": "swam", "fly": "flew", "drive": "drove",
    "ride": "rode", "buy": "bought", "bring": "brought", "build": "built",
    "break": "broke", "say": "said", "tell": "told", "read": "read"
}

PRONOUNS = {
    "i": {"nominative": "I", "accusative": "me", "possessive": "my", "reflexive": "myself"},
    "you": {"nominative": "You", "accusative": "you", "possessive": "your", "reflexive": "yourself"},
    "he": {"nominative": "He", "accusative": "him", "possessive": "his", "reflexive": "himself"},
    "she": {"nominative": "She", "accusative": "her", "possessive": "her", "reflexive": "herself"},
    "it": {"nominative": "It", "accusative": "it", "possessive": "its", "reflexive": "itself"},
    "we": {"nominative": "We", "accusative": "us", "possessive": "our", "reflexive": "ourselves"},
    "they": {"nominative": "They", "accusative": "them", "possessive": "their", "reflexive": "themselves"}
}

def get_article(word):
    """Smart 'a' vs 'an' logic with common exceptions."""
    if not word: return "a"
    w = word.lower().strip()
    # Exceptions
    if w.startswith(("hour", "honest", "heir", "honor")):
        return "an"
    if w.startswith(("uni", "use", "eu", "one")):
        return "a"
    # Vowel check
    if w[0] in "aeiou":
        return "an"
    return "a"

def pluralize(noun):
    """Converts singular nouns to plural."""
    n = noun.lower().strip()
    if n in IRREGULAR_NOUNS:
        return IRREGULAR_NOUNS[n]
    if n.endswith(("s", "x", "z", "ch", "sh")):
        return n + "es"
    if n.endswith("y") and len(n) > 1 and n[-2] not in "aeiou":
        return n[:-1] + "ies"
    if n.endswith("f") and not n.endswith(("ff", "oof", "ief")):
        return n[:-1] + "ves"
    if n.endswith("fe") and not n.endswith("ffe"):
        return n[:-2] + "ves"
    return n + "s"

def conjugate_verb(base_verb, tense="present", subject="it"):
    """Handles Present, Past, and Future tenses with subject agreement."""
    v = base_verb.lower().strip()
    subj = subject.lower().strip()

    if tense == "past":
        if v in IRREGULAR_VERBS_PAST:
            return IRREGULAR_VERBS_PAST[v]
        if v.endswith("e"): return v + "d"
        if v.endswith("y") and len(v) > 1 and v[-2] not in "aeiou": return v[:-1] + "ied"
        return v + "ed"

    elif tense == "future":
        return f"will {v}"

    else: # present
        if v == "be":
            if subj == "i": return "am"
            if subj in ("you", "we", "they") or subj.endswith("s"): return "are"
            return "is"
        if v == "have":
            if subj in ("i", "you", "we", "they") or subj.endswith("s"): return "have"
            return "has"
        if v == "do":
            if subj in ("i", "you", "we", "they") or subj.endswith("s"): return "do"
            return "does"
        if v == "did":
            return "did"
            
        # 1st/2nd person or plural subjects take base form
        if subj in ("i", "you", "we", "they") or subj.endswith("s"):
            return v
        # 3rd person singular takes 's' or 'es'
        if v.endswith(("s", "sh", "ch", "x", "z", "o")):
            return v + "es"
        if v.endswith("y") and len(v) > 1 and v[-2] not in "aeiou":
            return v[:-1] + "ies"
        return v + "s"

def get_pronoun(word, case="nominative"):
    """Returns the correct pronoun form (I, me, my, mine)."""
    w = word.lower().strip()
    if w in PRONOUNS:
        return PRONOUNS[w].get(case, word)
    return word


def normalize_pronoun(word):
    """Converts me/my/him to i/he for consistent parsing."""
    w = word.lower().strip()
    mapping = {"me": "i", "my": "i", "mine": "i", "him": "he", "his": "he", "her": "she", "hers": "she", "them": "they", "their": "they", "us": "we", "our": "we"}
    return mapping.get(w, w)


import re as _re

PRONOUN_SWAP_PATTERNS = [
    (r"\bI'm\b", "you are"),
    (r"\bI am\b", "you are"),
    (r"\bI\b", "you"),
    (r"\bmy\b", "your"),
    (r"\bme\b", "you"),
    (r"\bmine\b", "yours"),
    (r"\bmyself\b", "yourself"),
    (r"\bam\b", "are"),
]

def swap_pronouns(text):
    """Swaps first-person pronouns to second-person (NSM recalling user's memory)."""
    if not text:
        return text
    result = text
    for pattern, replacement in PRONOUN_SWAP_PATTERNS:
        result = _re.sub(pattern, replacement, result, flags=_re.IGNORECASE)
    return result
