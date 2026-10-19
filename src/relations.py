import re
import time
from src.patterns import is_svo_verb, to_base_verb

NOUN_DETERMINERS = {"a", "an", "the"}
AUX_VERBS = {"is","am","are","was","were","will","shall","has","have","had","do","does","did"}
STOP_TAIL = {"a","an","the","of","in","on","at","to","for",
             "with","by","from","and","or","but","is","are"}

CORRECTION_MARKERS = {"no","actually","wrong","correction","instead","not"}
REINFORCE_WORDS = {"yes","right","correct","exactly","true"}


def _tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def _pick_head_noun(tail_words):
    if not tail_words:
        return None
    for w in reversed(tail_words):
        if w not in STOP_TAIL and len(w) >= 2:
            return w
    return tail_words[-1] if tail_words else None


def extract(subject_word, definition_text, correction=False):
    words = _tokens(definition_text)
    subject = subject_word.lower().strip() if subject_word else None
    if not words or not subject:
        return []

    is_correction = correction or any(w in CORRECTION_MARKERS for w in words[:3])

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
            rels.append({"type": "HAS", "subject": subject, "object": obj, "correct": is_correction})
        return rels

    # SVO Extraction (e.g., salman likes mangoes)
    for i, w in enumerate(words):
        if is_svo_verb(w):
            obj = _pick_head_noun(words[i+1:])
            if obj and obj != subject:
                base_v = to_base_verb(w)
                rels.append({"type": base_v.upper(), "subject": subject, "object": obj, "correct": is_correction})
            return rels

    if "can" in words:
        i = words.index("can")
        obj = _pick_head_noun(words[i + 1:])
        if obj and obj != subject:
            rels.append({"type": "CAN", "subject": subject, "object": obj, "correct": is_correction})
        return rels

    if "means" in words or "mean" in words:
        i = max(words.index("means") if "means" in words else -1,
                words.index("mean") if "mean" in words else -1)
        obj_words = [w for w in words[i + 1:] if w not in STOP_TAIL]
        if obj_words:
            rels.append({"type": "IS", "subject": subject, "object": obj_words[0], "correct": is_correction})
        return rels

    if "is" in words or "are" in words:
        marker = "is" if "is" in words else "are"
        i = words.index(marker)
        tail = [w for w in words[i + 1:] if w not in NOUN_DETERMINERS and w not in CORRECTION_MARKERS]
        if not tail:
            return []
        head = _pick_head_noun(tail)
        if head and head != subject:
            rels.append({"type": "IS", "subject": subject, "object": head, "correct": is_correction})
        return rels

    return []


class RelationStore:
    def __init__(self):
        self.relations = {}  # (type, subject) -> {obj: record}

    def _rec(self, rel_type, subject, obj, correct=False):
        key = (rel_type, subject)
        if key not in self.relations:
            self.relations[key] = {}
        bucket = self.relations[key]
        now = time.time()
        if obj not in bucket:
            bucket[obj] = {"count": 1, "first_seen": now, "last_seen": now,
                           "superseded": False, "source": "user"}
        else:
            bucket[obj]["count"] += 1
            bucket[obj]["last_seen"] = now
            bucket[obj]["superseded"] = False

        if correct:
            for other, rec in bucket.items():
                if other != obj:
                    rec["superseded"] = True

    def add(self, rel_type, subject, obj, correct=False):
        self._rec(rel_type, subject, obj, correct)

    def get(self, rel_type, subject, include_superseded=False):
        bucket = self.relations.get((rel_type, subject), {})
        return sorted([o for o, r in bucket.items()
                       if include_superseded or not r["superseded"]])

    def active_count(self):
        n = 0
        for bucket in self.relations.values():
            for rec in bucket.values():
                if not rec["superseded"]:
                    n += 1
        return n

    def query(self, rel_type, subject, obj):
        bucket = self.relations.get((rel_type, subject))
        if not bucket:
            has_subject = any(s == subject for (t, s) in self.relations.keys())
            if has_subject:
                return ("no", [])
            return ("unknown_subject", None)
        target = bucket.get(obj)
        if target and not target["superseded"]:
            return ("yes", target)
        if target and target["superseded"]:
            return ("superseded", target)
        active = [o for o, r in bucket.items() if not r["superseded"]]
        if active:
            return ("no", active)
        return ("no", [])

    def history(self, rel_type, subject):
        bucket = self.relations.get((rel_type, subject), {})
        return {obj: dict(rec) for obj, rec in bucket.items()}

    def count(self):
        return self.active_count()

    def all(self):
        out = {}
        for key, bucket in self.relations.items():
            active = [o for o, r in bucket.items() if not r["superseded"]]
            if active:
                out[key] = sorted(active)
        return out


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
    if words[0] == "what" and len(words) >= 4 and words[1] in ("does", "do"):
        subj = words[2]
        verb = words[3]
        if is_svo_verb(verb):
            return ("SVO", subj, to_base_verb(verb))

    if words[0] == "can" and len(words) >= 3:
        core_words = [w for w in words[1:] if w not in NOUN_DETERMINERS]
        if len(core_words) >= 2:
            subj = core_words[0]
            obj = _pick_head_noun(core_words[1:])
            if subj and obj:
                return ("CAN", subj, obj)
            
    if words[0] == "does" and len(words) >= 3 and "have" not in words:
        subj = words[1]
        obj = _pick_head_noun(words[2:])
        if subj and obj:
            return ("CAN", subj, obj)

    if words[0] == "does" and "have" in words:
        i = words.index("have")
        subj_cand = [w for w in words[1:i] if w not in NOUN_DETERMINERS]
        if subj_cand:
            subj = subj_cand[-1]
            obj = _pick_head_noun(words[i + 1:])
            if subj and obj:
                return ("HAS", subj, obj)
    return None
