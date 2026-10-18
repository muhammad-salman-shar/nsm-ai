# L3.1: Reusable SVO pattern rules

BASE_VERBS = {
    "like", "love", "want", "need", "eat", "drink",
    "play", "see", "know", "think", "feel", "find", "make"
}

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

def is_svo_verb(word):
    w = word.lower()
    if w in BASE_VERBS:
        return True
    # Handle 3rd person forms (likes -> like)
    if w.endswith("s") and w[:-1] in BASE_VERBS:
        return True
    return False

def to_base_verb(word):
    w = word.lower()
    if w.endswith("s") and w[:-1] in BASE_VERBS:
        return w[:-1]
    return w
