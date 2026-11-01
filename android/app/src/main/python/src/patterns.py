# L3.1: Reusable SVO pattern rules

BASE_VERBS = {
    "like", "love", "want", "need", "eat", "drink",
    "play", "see", "know", "think", "feel", "find", "make", "go", "run", "take", "give", "write", "read", "swim", "fly", "drive", "ride", "buy", "bring", "build", "break", "say", "tell"
}

IRREGULAR_PAST = {
    "ate":"eat", "went":"go", "saw":"see", "ran":"run", "made":"make",
    "took":"take", "gave":"give", "knew":"know", "thought":"think", "felt":"feel",
    "found":"find", "drank":"drink", "wrote":"write", "swam":"swim", "flew":"fly",
    "drove":"drive", "rode":"ride", "bought":"buy", "brought":"bring", "built":"build",
    "broke":"break", "said":"say", "told":"tell", "read":"read"
}

def get_base_verb(word):
    w = word.lower()
    if w in BASE_VERBS: return w
    if w in IRREGULAR_PAST: return IRREGULAR_PAST[w]
    if w.endswith("s") and w[:-1] in BASE_VERBS: return w[:-1]
    if w.endswith("ed"):
        if w[:-2] in BASE_VERBS: return w[:-2]
        if w[:-1] in BASE_VERBS: return w[:-1]
    if w.endswith("ing"):
        if w[:-3] in BASE_VERBS: return w[:-3]
        if w[:-3]+"e" in BASE_VERBS: return w[:-3]+"e"
    return None

def is_svo_verb(word):
    return get_base_verb(word) is not None

def to_base_verb(word):
    base = get_base_verb(word)
    return base if base else word.lower()

from src.morphology import conjugate_verb

def conjugate(verb, subject):
    """Wrapper for backward compatibility."""
    return conjugate_verb(verb, tense="present", subject=subject)




def get_tense_and_base(word):
    """Returns (base_verb, tense). Handles will eat, is eating, ate, etc."""
    if word.endswith("ing"):
        return word[:-3], "continuous"
    if word in ("will", "shall"):
        return word, "future"
    # For simplicity, let's just treat standard SVO as present for now
    return word, "present"
