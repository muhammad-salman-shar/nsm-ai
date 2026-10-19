import hashlib
import numpy as np

FEATURES = 500
INTENTS = ["greeting", "question", "statement", "sad", "happy",
           "farewell", "identity", "unknown"]


def _stable_hash(s, mod):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % mod


def featurize(text, n_features=FEATURES):
    v = np.zeros(n_features, dtype=np.float32)
    words = text.lower().split()
    for w in words:
        v[_stable_hash("w:" + w, n_features)] += 1.0
    for a, b in zip(words, words[1:]):
        v[_stable_hash("b:" + a + "_" + b, n_features)] += 1.0
    n = np.linalg.norm(v)
    if n > 0:
        v /= n
    return v


class Perceptron:
    def __init__(self, n_features=FEATURES, n_classes=len(INTENTS), lr=0.1):
        self.n_features = n_features
        self.n_classes = n_classes
        self.lr = lr
        rng = np.random.default_rng(42)
        self.W = rng.normal(0, 0.01, (n_features, n_classes)).astype(np.float32)
        self.b = np.zeros(n_classes, dtype=np.float32)

    def forward(self, x):
        logits = x @ self.W + self.b
        logits = logits - logits.max()
        e = np.exp(logits)
        return e / e.sum()

    def predict(self, text):
        probs = self.forward(featurize(text, self.n_features))
        idx = int(np.argmax(probs))
        return INTENTS[idx], float(probs[idx])

    def train_step(self, text, label):
        x = featurize(text, self.n_features)
        y = INTENTS.index(label)
        probs = self.forward(x)
        grad = probs.copy()
        grad[y] -= 1.0
        self.W -= self.lr * np.outer(x, grad)
        self.b -= self.lr * grad
        return float(-np.log(probs[y] + 1e-9))

    def train(self, data, epochs=300):
        losses = []
        for ep in range(epochs):
            total = 0.0
            for text, label in data:
                total += self.train_step(text, label)
            if ep % 50 == 0:
                losses.append((ep, total / len(data)))
        return losses

    def save(self, path):
        p = path if path.endswith(".npz") else path + ".npz"
        np.savez(p, W=self.W, b=self.b)

    def load(self, path):
        p = path if path.endswith(".npz") else path + ".npz"
        d = np.load(p)
        self.W = d["W"]
        self.b = d["b"]


TRAINING_DATA = [
    ("hi", "greeting"), ("hello", "greeting"), ("hey there", "greeting"),
    ("good morning", "greeting"), ("hello nsm", "greeting"), ("hi hi", "greeting"),
    ("what is your name", "identity"), ("who are you", "identity"),
    ("who made you", "identity"), ("what are you", "identity"),
    ("your name please", "identity"), ("who built you", "identity"),
    ("how are you", "question"), ("what is 2 plus 2", "question"),
    ("what time is it", "question"), ("can you help me", "question"),
    ("why is the sky blue", "question"), ("do you like mangoes", "question"),
    ("i am sad", "sad"), ("i feel terrible", "sad"),
    ("i am crying", "sad"), ("i miss my friend", "sad"), ("i feel lonely", "sad"),
    ("i am happy", "happy"), ("yay i won", "happy"), ("i love mangoes", "happy"),
    ("this is great", "happy"), ("i feel amazing", "happy"),
    ("bye", "farewell"), ("goodbye", "farewell"), ("see you later", "farewell"),
    ("good night", "farewell"), ("talk to you later", "farewell"),
    ("i like games", "statement"), ("the sky is blue", "statement"),
    ("i have a dog", "statement"), ("my name is salman", "statement"),
    ("dogs bark", "statement"),
    ("asdfghjkl", "unknown"), ("nonsense text here", "unknown"),
    ("qwerty random", "unknown"), ("xyz abc", "unknown"),
]
