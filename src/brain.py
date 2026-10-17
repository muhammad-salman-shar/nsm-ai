import re
from src.affect import Affect
from src.personality import Personality
from src.memory import Lexicon, EpisodicMemory
from src.perceptron import Perceptron, TRAINING_DATA
from src.language import Language
from src.relations import (extract, parse_query, RelationStore,
                           CORRECTION_MARKERS, NOUN_DETERMINERS, STOP_TAIL)

MATH_WORDS = {"zero":0,"one":1,"two":2,"three":3,"four":4,
              "five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}

DEFAULT_MAX_DEPTH = 5
HARD_MAX_DEPTH = 8

_GRAMMAR = {
    "a","an","the","is","are","am","was","were","be","been","being",
    "i","you","we","they","he","she","it","me","my","your","our","their","its",
    "to","of","in","on","at","for","with","by","from","about","into",
    "and","or","but","if","then","so","because","as","than","also","too",
    "do","does","did","done","have","has","had",
    "will","would","can","could","should","may","might","must","shall",
    "what","who","why","how","when","where","which","whose",
    "this","that","these","those","there","here",
    "not","no","yes","ok","okay","sure","please",
    "hi","hello","hey","bye","goodbye","greetings",
    "one","two","three","four","five","six","seven","eight","nine","ten","zero",
    "plus","minus","times","multiplied","divided",
}

_COMMON_VERBS = {
    "saw","see","seen","look","looked","looks",
    "go","went","gone","goes","come","came","comes",
    "say","said","says","tell","told","tells",
    "make","made","makes","get","got","gets",
    "take","took","takes","give","gave","gives",
    "know","knew","knows","think","thought","thinks",
    "feel","felt","feels","find","found","finds",
    "ask","asked","asks","work","worked","works",
    "play","played","plays","want","wanted","wants",
    "need","needed","needs","help","helped","helps",
    "put","use","used","try","tried","call","called",
    "eat","ate","drink","drank","sleep","slept",
    "live","lived","learn","learned","understand","understood",
    "remember","remembered","forget","forgot","show","showed",
    "bring","brought","buy","bought","sell","sold",
    "build","built","break","broke","start","started",
    "stop","stopped","open","opened","close","closed",
    "sit","sat","stand","stood","wait","waited",
    "meet","met","carry","carried","hold","held",
    "hit","cut","kill","killed","die","died",
    "win","won","lose","lost","write","wrote",
    "read","sing","sang","dance","danced","jump","jumped",
    "fly","flew","swim","swam","drive","drove","ride","rode",
    "climb","climbed","fall","fell","laugh","laughed",
    "cry","cried","smile","smiled","hope","hoped",
    "wish","wished","decide","decided","explain","explained",
    "means","mean","meaning","meant","known",
    "actually","wrong","correction","instead","alright",
}

_QUESTION_STARTERS = {
    "what","who","where","when","why","how","which","whose",
    "tell","explain","define",
    "do","does","did","can","could","will","would","should",
    "is","are","was","were","have","has","had","may","might","must",
}

def _build_stopwords():
    words = set(_GRAMMAR) | set(_COMMON_VERBS)
    for text, _ in TRAINING_DATA:
        for w in re.findall(r"[a-z]+", text.lower()):
            words.add(w)
    return words

STOPWORDS = _build_stopwords()


def _words(text):
    return re.findall(r"[a-z]+", text.lower())


def _to_int(tok):
    return int(tok) if tok.isdigit() else MATH_WORDS.get(tok)


def _is_question_text(text):
    words = _words(text)
    return bool(words) and words[0] in _QUESTION_STARTERS


class Brain:
    def __init__(self, perceptron_path="src/perceptron.npz",
                 max_depth=DEFAULT_MAX_DEPTH):
        self.affect = Affect()
        self.personality = Personality
        self.lexicon = Lexicon()
        self.episodic = EpisodicMemory()
        self.perceptron = Perceptron()
        self.lang = Language(seed=7)
        self.relations = RelationStore()
        self.max_depth = min(int(max_depth), HARD_MAX_DEPTH)
        self._boot_perceptron(perceptron_path)
        self._seed_lexicon("data/stimuli.txt")
        self.turn = 0
        self.pending = None
        self.definitions = {}
        self.ask_depth = 0
        self.asked_words = set()

    def _boot_perceptron(self, path):
        try:
            self.perceptron.load(path)
        except (FileNotFoundError, OSError):
            self.perceptron.train(TRAINING_DATA, epochs=300)
            try:
                self.perceptron.save(path)
            except OSError:
                pass

    def _seed_lexicon(self, path):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        self.lexicon.see(parts[0], parts[1:])
        except FileNotFoundError:
            pass

    def _try_math(self, text):
        t = text.lower()
        t = t.replace("plus", "+").replace("minus", "-")
        t = t.replace("times", "*").replace("multiplied by", "*")
        toks = t.split()
        for i, op in enumerate(toks):
            if op in ("+", "-", "*") and 0 < i < len(toks) - 1:
                a, b = _to_int(toks[i - 1]), _to_int(toks[i + 1])
                if a is not None and b is not None:
                    return {"+": a + b, "-": a - b, "*": a * b}[op]
        m = re.search(r"(\d+)\s*([+\-*])\s*(\d+)", t)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            return {"+": a + b, "-": a - b, "*": a * b}[op]
        return None

    def _perceive(self, text):
        words = _words(text)
        intent, conf = self.perceptron.predict(text)
        if conf < 0.40:
            intent = "unknown"
        return words, intent, conf

    def _is_unknown(self, w):
        if w in STOPWORDS:
            return False
        if len(w) < 3:
            return False
        if self.lexicon.has(w):
            return False
        if w in self.definitions:
            return False
        return True

    def _find_unknown(self, words):
        seen, unknown = set(), []
        for w in words:
            if w in seen:
                continue
            seen.add(w)
            if self._is_unknown(w):
                unknown.append(w)
        unknown.sort(key=lambda w: -len(w))
        return unknown

    def _attend(self, words):
        known = sum(1 for w in words if self.lexicon.has(w))
        ratio = known / max(len(words), 1)
        if ratio < 0.3:
            self.affect.event("new_input", intensity=0.25)
        else:
            self.affect.event("familiar_input", intensity=ratio)
        return ratio

    def _bind_words(self, words):
        if not words:
            return
        for i, w in enumerate(words):
            ctx = [words[j] for j in range(len(words)) if j != i][:2]
            self.lexicon.see(w, ctx)

    def _lookup_definition(self, text):
        q = _words(text)
        if not any(w in ("what","who","tell","explain","define") for w in q):
            return None
        for w in q:
            if w in self.definitions:
                return f"{w} means: {self.definitions[w]}"
        return None

    def _generate(self, intent, conf, text, recall):
        math = self._try_math(text)
        if math is not None:
            self.affect.event("rewarded", intensity=0.5)
            return f"The answer is {math}."
        rel_query = parse_query(text)
        if rel_query:
            rel_type, subj, obj = rel_query
            verb = "is" if rel_type == "IS" else "has"
            status, detail = self.relations.query(rel_type, subj, obj)
            if status == "yes":
                return f"Yes, {subj} {verb} {obj}."
            if status == "superseded":
                active = self.relations.get(rel_type, subj)
                if active:
                    return f"No, {subj} {verb} {', '.join(active)}, not {obj}."
                return f"No, {subj} {verb} {obj} is outdated."
            if status == "no":
                if detail:
                    return f"I know {subj} {verb} {', '.join(detail)}. But I don't know if {subj} {verb} {obj}."
                return f"No, {subj} {verb} {', '.join(detail)}." if detail else f"I don't know."
            return f"I don't know {subj} yet. Teach me?"
        lookup = self._lookup_definition(text)
        if lookup:
            return lookup
        if recall and recall[0][1] > 0.50 and intent != "identity":
            past = recall[0][0]["text"]
            pw = set(past.lower().split())
            tw = set(text.lower().split())
            if pw & tw:
                return f"I remember you said '{past}'. " + self.lang.generate(intent, self.personality, self.affect)
        return self.lang.generate(intent, self.personality, self.affect)

    def _reset_chain(self):
        self.ask_depth = 0
        self.asked_words.clear()

    def _try_learn_relation(self, text):
        words = _words(text)
        if len(words) < 3:
            return None
        for m in ("means", "is", "are", "has"):
            if m not in words:
                continue
            idx = words.index(m)
            pre = [w for w in words[:idx] if w not in NOUN_DETERMINERS and w not in STOPWORDS]
            post = [w for w in words[idx+1:] if w not in NOUN_DETERMINERS and w not in STOP_TAIL]
            if not pre or not post:
                continue
            subject = pre[-1]
            if len(subject) < 3:
                continue
            if not self.lexicon.has(subject) and subject not in self.definitions:
                self.definitions[subject] = text.strip()
                self.lexicon.see(subject, post[:3])
            rels = extract(subject, text)
            if not rels:
                continue
            for rel in rels:
                self.relations.add(rel["type"], rel["subject"], rel["object"], rel["correct"])
                if rel["object"] and not self.lexicon.has(rel["object"]):
                    self.lexicon.see(rel["object"])
            return f"Got it! I learned that {subject} {m} {' '.join(post[:3])}."
        return None

    def _answer_question(self, text):
        words, intent, conf = self._perceive(text)
        self._attend(words)
        lookup = self._lookup_definition(text)
        if lookup:
            response = lookup
        else:
            recall = self.episodic.recall(text, top_k=1)
            response = self._generate(intent, conf, text, recall)
        self._bind_words(words)
        self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
        self.affect.tick()
        return {
            "turn": self.turn, "text": text, "intent": intent,
            "confidence": round(conf, 3), "mood": self.affect.mood(),
            "recall": None, "response": response,
        }

    def _resolve_pending(self, text):
        word, original = self.pending
        self.pending = None
        definition = text.strip()
        w_lower = (word or "").lower()

        def_unknown = [w for w in _words(definition)
                       if w != w_lower and self._is_unknown(w)]
        orig_unknown = [w for w in _words(original)
                        if w != w_lower and self._is_unknown(w)]

        if word is None:
            key = f"_phrase:{original.lower()[:40]}"
            self.definitions[key] = definition
            label = "phrase"
        else:
            self.definitions[word] = definition
            label = word
            self.lexicon.see(word, _words(definition)[:3])
            for rel in extract(word, definition):
                self.relations.add(rel["type"], rel["subject"], rel["object"], rel["correct"])
                if rel["object"] and not self.lexicon.has(rel["object"]):
                    self.lexicon.see(rel["object"])

        self.episodic.store(f"learned {label}: {definition}", "curious", "[learned]", 1.0)
        self.affect.event("rewarded", intensity=0.8)

        seen = set()
        candidates = []
        for w in def_unknown + orig_unknown:
            if w not in seen and w not in self.asked_words:
                seen.add(w)
                candidates.append(w)
        candidates.sort(key=lambda w: -len(w))

        if candidates and self.ask_depth < self.max_depth:
            nw = candidates[0]
            self.pending = (nw, original)
            self.ask_depth += 1
            self.asked_words.add(nw)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 0, "mood": self.affect.mood(), "recall": None,
                "response": f"Got it! But what is '{nw}'?",
                "defined": label,
            }

        self._reset_chain()
        words, intent, conf = self._perceive(original)
        self._attend(words)
        self._bind_words(words)
        recall = self.episodic.recall(original, top_k=1)
        if intent == "unknown" or conf < 0.40:
            response = f"Got it! Now I know about '{label}'. Thanks for teaching me!"
        else:
            response = "Got it! " + self._generate(intent, conf, original, recall)
        self.episodic.store(original, self.affect.mood(), response, self.affect.binding_strength())
        self.affect.tick()
        return {
            "turn": self.turn, "text": text, "intent": intent,
            "confidence": round(conf, 3), "mood": self.affect.mood(),
            "recall": recall[0][0]["text"] if recall else None,
            "response": response, "defined": label,
        }

    def observe(self, text):
        self.turn += 1

        if self.pending and _is_question_text(text):
            self.pending = None
            self._reset_chain()
            return self._answer_question(text)

        if self.pending:
            return self._resolve_pending(text)

        learned_resp = self._try_learn_relation(text)
        if learned_resp:
            words_lr = _words(text)
            self._attend(words_lr)
            self._bind_words(words_lr)
            self.episodic.store(text, self.affect.mood(), learned_resp, self.affect.binding_strength())
            self.affect.event("rewarded", intensity=0.5)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "statement",
                "confidence": 0, "mood": self.affect.mood(), "recall": None,
                "response": learned_resp,
            }

        words, intent, conf = self._perceive(text)
        self._attend(words)
        recall = self.episodic.recall(text, top_k=1)

        if parse_query(text) is None:
            unknown = self._find_unknown(words)
        else:
            unknown = []
        if unknown and self.ask_depth < self.max_depth:
            word = unknown[0]
            self.pending = (word, text)
            self.ask_depth += 1
            self.asked_words.add(word)
            self.affect.event("new_input", intensity=0.8)
            self._bind_words(words)
            self.episodic.store(text, self.affect.mood(), f"[asked about '{word}']", 0.5)
            self.affect.tick()
            return {
                "turn": self.turn, "text": text, "intent": "question",
                "confidence": 0, "mood": self.affect.mood(), "recall": None,
                "response": f"I don't know the word '{word}'. What does it mean?",
            }

        self._bind_words(words)
        known_ratio = sum(1 for w in words if self.lexicon.has(w)) / max(len(words), 1)
        if known_ratio > 0.5 and intent != "unknown":
            self.affect.event("repeated", intensity=0.6)

        response = self._generate(intent, conf, text, recall)
        self.episodic.store(text, self.affect.mood(), response, self.affect.binding_strength())
        self.affect.tick()

        for k in ("curiosity", "attention"):
            if self.affect.drives[k] > 85:
                self.affect.drives[k] = 78
        if self.affect.drives["curiosity"] > 65 and self.turn > 3:
            self.affect.drives["curiosity"] -= 8

        return {
            "turn": self.turn, "text": text, "intent": intent,
            "confidence": round(conf, 3), "mood": self.affect.mood(),
            "recall": recall[0][0]["text"] if recall else None,
            "response": response,
        }

    def state(self):
        return {
            "turn": self.turn,
            "mood": self.affect.mood(),
            "episodes": self.episodic.size(),
            "vocab": len(self.lexicon.words),
            "definitions": len(self.definitions),
            "relations": self.relations.count(),
            "pending": self.pending,
            "max_depth": self.max_depth,
            "ask_depth": self.ask_depth,
            "affect": dict(self.affect.drives),
            "hormones": dict(self.affect.hormones),
        }
