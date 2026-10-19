import json
import time
import numpy as np

DIM = 10000
_rng = np.random.default_rng(1337)
_cache = {}

def _vec(symbol):
    s = str(symbol)
    if s not in _cache:
        _cache[s] = _rng.integers(0, 2, size=DIM, dtype=np.uint8)
    return _cache[s]

def bind(*symbols):
    v = np.zeros(DIM, dtype=np.uint8)
    for s in symbols:
        v = v ^ _vec(s)
    return v

def bundle(vectors):
    if not vectors:
        return np.zeros(DIM, dtype=np.uint8)
    arr = np.stack(vectors)
    return (arr.sum(axis=0) > (len(vectors) / 2)).astype(np.uint8)

def similarity(a, b):
    return float(np.mean(a == b))

def hamming(a, b):
    return int(np.sum(a != b))

class Lexicon:
    def __init__(self):
        self.words = {}
        self.count = 0

    def see(self, word, context=None):
        w = word.lower().strip()
        if not w:
            return None
        self.count += 1
        if w not in self.words:
            self.words[w] = {"relations": {}, "vec": _vec(w)}
        if context:
            for c in context:
                cs = str(c).lower()
                if cs == w:
                    continue
                if cs not in self.words:
                    self.words[cs] = {"relations": {}, "vec": _vec(cs)}
                rel = bind(w, cs)
                self.words[w]["relations"][cs] = rel
                self.words[cs]["relations"][w] = rel
        return self.words[w]["vec"]

    def learn(self, word, contexts):
        for c in contexts:
            self.see(word, [c])
        return self.words[word.lower().strip()]["vec"]

    def meaning(self, word, top_k=5):
        w = word.lower().strip()
        if w not in self.words:
            return []
        relations = self.words[w]["relations"]
        if not relations:
            return []
        w_vec = _vec(w)
        recovered = [rel ^ w_vec for rel in relations.values()]
        scored = []
        for candidate, data in self.words.items():
            if candidate == w:
                continue
            cand_vec = data["vec"]
            best = max(similarity(r, cand_vec) for r in recovered)
            scored.append((candidate, best))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def correct(self, word, old_context, new_context):
        w = word.lower().strip()
        oc = old_context.lower().strip()
        if w in self.words:
            self.words[w]["relations"].pop(oc, None)
            if oc in self.words:
                self.words[oc]["relations"].pop(w, None)
        self.see(word, [new_context])

    def has(self, word):
        return word.lower().strip() in self.words


class EpisodicMemory:
    def __init__(self):
        self.episodes = []

    def store(self, text, mood, response, binding_strength=1.0):
        words = [w for w in text.lower().split() if w]
        vec = bundle([_vec(w) for w in words]) if words else np.zeros(DIM, dtype=np.uint8)
        ep = {
            "t": time.time(),
            "text": text,
            "mood": mood,
            "response": response,
            "strength": float(binding_strength),
            "vec": vec,
            "words": list(words),
        }
        self.episodes.append(ep)
        return ep

    def recall(self, text, top_k=3):
        if not self.episodes or not text:
            return []
        q_words = set(w for w in text.lower().split() if w)
        if not q_words:
            return []
        q_vec = bundle([_vec(w) for w in q_words])
        scored = []
        for ep in self.episodes:
            ep_words = set(ep["words"])
            hdc = similarity(ep["vec"], q_vec)
            overlap = len(ep_words & q_words) / max(len(q_words), 1)
            score = 0.4 * hdc + 0.6 * overlap
            scored.append((ep, score))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def size(self):
        return len(self.episodes)

    def save(self, path):
        data = [{k: v for k, v in ep.items() if k != "vec"} for ep in self.episodes]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path):
        try:
            with open(path) as f:
                data = json.load(f)
            self.episodes = []
            for ep in data:
                ep["vec"] = bundle([_vec(w) for w in ep["words"]])
                self.episodes.append(ep)
        except FileNotFoundError:
            pass
