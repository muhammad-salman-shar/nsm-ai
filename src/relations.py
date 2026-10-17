import re

NOUN_DETERMINERS = {"a", "an", "the"}
ADJECTIVE_HINTS = {"very", "really", "quite", "so", "too", "kind", "sort"}

STOP_TAIL = {"a", "an", "the", "of", "in", "on", "at", "to", "for",
             "with", "by", "from", "and", "or", "but", "is", "are"}


def _tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def _pick_head_noun(tail_words):
    if not tail_words:
        return None
    for w in reversed(tail_words):
        if w not in STOP_TAIL and len(w) >= 2:
            return w
    return tail_words[-1] if tail_words else None


def extract(subject_word, definition_text):
    words = _tokens(definition_text)
    subject = subject_word.lower().strip() if subject_word else None
    if not words or not subject:
        return []

    if subject in words:
        idx = words.index(subject)
        words = words[idx + 1:]
    if not words:
        return []

    rels = []

    if "has" in words:
        i = words.index("has")
        obj = _pick_head_noun(words[i + 1:])
        if obj and obj != subject:
            rels.append(("HAS", subject, obj))
        return rels

    if "means" in words or "mean" in words:
        i = max(words.index("means") if "means" in words else -1,
                words.index("mean") if "mean" in words else -1)
        obj_words = [w for w in words[i + 1:] if w not in STOP_TAIL]
        if obj_words:
            rels.append(("IS", subject, obj_words[0]))
        return rels

    if "is" in words or "are" in words:
        marker = "is" if "is" in words else "are"
        i = words.index(marker)
        tail = [w for w in words[i + 1:] if w not in NOUN_DETERMINERS]
        if not tail:
            return []
        head = _pick_head_noun(tail)
        if head and head != subject:
            rels.append(("IS", subject, head))
        return rels

    return []


class RelationStore:
    def __init__(self):
        self.relations = {}

    def add(self, rel_type, subject, obj):
        key = (rel_type, subject)
        self.relations.setdefault(key, set()).add(obj)

    def get(self, rel_type, subject):
        return sorted(self.relations.get((rel_type, subject), set()))

    def has(self, rel_type, subject, obj):
        return obj in self.relations.get((rel_type, subject), set())

    def all(self):
        return {k: sorted(v) for k, v in self.relations.items()}

    def count(self):
        return sum(len(v) for v in self.relations.values())

def parse_query(text):
    words = _tokens(text)
    if not words:
        return None
    if words[0] == "is" and len(words) >= 3:
        tail = [w for w in words[1:] if w not in NOUN_DETERMINERS]
        if len(tail) >= 2:
            subj = tail[0]
            obj = _pick_head_noun(tail[1:])
            if subj and obj and subj != obj:
                return ("IS", subj, obj)
    if words[0] == "does" and "have" in words:
        i = words.index("have")
        subj_cand = [w for w in words[1:i] if w not in NOUN_DETERMINERS]
        if subj_cand:
            subj = subj_cand[-1]
            obj = _pick_head_noun(words[i + 1:])
            if subj and obj:
                return ("HAS", subj, obj)
    return None
