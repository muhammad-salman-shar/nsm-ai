import re
from src.affect import Affect
from src.personality import Personality
from src.memory import Lexicon, EpisodicMemory
from src.perceptron import Perceptron, TRAINING_DATA
from src.language import Language

MATH_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
              "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
INTENTS = ["greeting", "question", "statement", "sad", "happy",
           "farewell", "identity", "unknown"]


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _to_int(tok):
    return int(tok) if tok.isdigit() else MATH_WORDS.get(tok)


class Brain:
    def __init__(self, perceptron_path="src/perceptron.npz"):
        self.affect = Affect()
        self.personality = Personality
        self.lexicon = Lexicon()
        self.episodic = EpisodicMemory()
        self.perceptron = Perceptron()
        self.lang = Language(seed=7)
        self._boot_perceptron(perceptron_path)
        self.turn = 0

    def _boot_perceptron(self, path):
        try:
            self.perceptron.load(path)
        except (FileNotFoundError, OSError):
            self.perceptron.train(TRAINING_DATA, epochs=300)
            try:
                self.perceptron.save(path)
            except OSError:
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

    def _generate(self, intent, conf, text, recall):
        math = self._try_math(text)
        if math is not None:
            self.affect.event("rewarded", intensity=0.5)
            return f"The answer is {math}."
        if recall and recall[0][1] > 0.50 and intent != "identity":
            past = recall[0][0]["text"]
            past_words = set(past.lower().split())
            text_words = set(text.lower().split())
            if past_words & text_words and len(past_words & text_words) >= 1:
                return f"I remember you said '{past}'. " + self.lang.generate(intent, self.personality, self.affect)
        return self.lang.generate(intent, self.personality, self.affect)

    def observe(self, text):
        self.turn += 1
        words, intent, conf = self._perceive(text)
        known_ratio = self._attend(words)
        recall = self.episodic.recall(text, top_k=1)
        self._bind_words(words)
        if known_ratio > 0.5 and intent != "unknown":
            self.affect.event("repeated", intensity=0.6)
        response = self._generate(intent, conf, text, recall)
        binding = self.affect.binding_strength()
        self.episodic.store(text, self.affect.mood(), response, binding)
        self.affect.tick()
        for k in ("curiosity", "attention"):
            if self.affect.drives[k] > 85:
                self.affect.drives[k] = 78
        if self.affect.drives["curiosity"] > 65 and self.turn > 3:
            self.affect.drives["curiosity"] -= 8
        return {
            "turn": self.turn,
            "text": text,
            "intent": intent,
            "confidence": round(conf, 3),
            "mood": self.affect.mood(),
            "recall": recall[0][0]["text"] if recall else None,
            "response": response,
        }

    def state(self):
        return {
            "turn": self.turn,
            "mood": self.affect.mood(),
            "episodes": self.episodic.size(),
            "vocab": len(self.lexicon.words),
            "affect": dict(self.affect.drives),
            "hormones": dict(self.affect.hormones),
        }
