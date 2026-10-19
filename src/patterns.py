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

def conjugate(verb, subject):
    """Returns the correct present-tense form of the verb for the subject."""
    subj = subject.lower()
    v = verb.lower()

    # 1st/2nd person or plural -> base form
    if subj in ("i", "you", "we", "they"):
        return v

    # 3rd person singular (he, she, it, salman, dog, etc.)
    if v.endswith("s") or v.endswith("sh") or v.endswith("ch") or v.endswith("x") or v.endswith("o"):
        return v + "es"
    elif v.endswith("y") and len(v) > 1 and v[-2] not in "aeiou":
        return v[:-1] + "ies"
    else:
        return v + "s"




def conjugate_past(verb):
    v = verb.lower()
    if v.endswith("e"): return v + "d"
    if v.endswith("y") and v[-2] not in "aeiou": return v[:-1] + "ied"
    # Common irregular verbs
    irregulars = {"eat": "ate", "go": "went", "see": "saw", "run": "ran", "do": "did", "have": "had", "make": "made", "take": "took", "is": "was", "are": "were"}
    if v in irregulars: return irregulars[v]
    return v + "ed"

def get_tense_and_base(word):
    """Returns (base_verb, tense). Handles will eat, is eating, ate, etc."""
    if word.endswith("ing"):
        return word[:-3], "continuous"
    if word in ("will", "shall"):
        return word, "future"
    # For simplicity, let's just treat standard SVO as present for now
    return word, "present"
