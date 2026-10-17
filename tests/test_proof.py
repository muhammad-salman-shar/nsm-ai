import unittest
import numpy as np
from src.memory import Lexicon, EpisodicMemory, bind, bundle, similarity
from src.perceptron import Perceptron, TRAINING_DATA


class TestAssociationLearning(unittest.TestCase):
    def test_cat_meow(self):
        lx = Lexicon()
        lx.see("cat", ["meow"])
        lx.see("dog", ["bark"])
        top = lx.meaning("meow")
        self.assertEqual(top[0][0], "cat",
                         f"expected cat to say meow, got {top[:3]}")
        self.assertAlmostEqual(top[0][1], 1.0, places=2)
        top2 = lx.meaning("bark")
        self.assertEqual(top2[0][0], "dog")


class TestDelayedRecall(unittest.TestCase):
    def test_100_interactions_later(self):
        em = EpisodicMemory()
        em.store("i like mangoes", "happy", "me too", 0.9)
        for i in range(100):
            em.store(f"chatter {i}", "neutral", "ok", 0.3)
        top = em.recall("do you like mangoes")
        self.assertEqual(top[0][0]["text"], "i like mangoes",
                         f"expected mangoes recall, got {top[0][0]['text']}")
        self.assertGreater(top[0][1], 0.5)


class TestGeneralization(unittest.TestCase):
    def test_new_instance_joins_category(self):
        lx = Lexicon()
        for fruit in ["apple", "banana", "mango"]:
            lx.see(fruit, ["fruit"])
        lx.see("orange", ["fruit"])
        top = lx.meaning("orange")
        self.assertEqual(top[0][0], "fruit")
        top_f = lx.meaning("fruit")
        names = [w for w, _ in top_f[:4]]
        for f in ["apple", "banana", "mango", "orange"]:
            self.assertIn(f, names, f"{f} missing from fruit category")


class TestCorrection(unittest.TestCase):
    def test_old_fact_superseded(self):
        lx = Lexicon()
        lx.see("sky", ["green"])
        self.assertEqual(lx.meaning("sky")[0][0], "green")
        lx.correct("sky", "green", "blue")
        top = lx.meaning("sky")
        self.assertEqual(top[0][0], "blue",
                         f"correction failed, got {top[:3]}")
        self.assertAlmostEqual(top[0][1], 1.0, places=2)
        scores = dict(top)
        self.assertLess(scores.get("green", 0.0), 0.65,
                        f"green still strongly associated: {scores.get('green')}")
        green_top = lx.meaning("green")
        if green_top:
            self.assertLess(green_top[0][1], 0.65,
                            f"green still strongly recalls something: {green_top[:2]}")


class TestHDCCollision(unittest.TestCase):
    def test_unrelated_pairs_dont_collide(self):
        pairs = [("cat", "car"), ("dog", "log"), ("red", "bed"),
                 ("sun", "bun"), ("moon", "spoon")]
        for a, b in pairs:
            v1 = bind(a, "x")
            v2 = bind(b, "x")
            s = similarity(v1, v2)
            self.assertLess(s, 0.65, f"{a}/{b} collide at {s:.3f}")
            self.assertGreater(s, 0.35, f"{a}/{b} too distant at {s:.3f}")


class TestDecodeFidelity(unittest.TestCase):
    def test_unbind_recovery(self):
        lx = Lexicon()
        for w, c in [("cat", "meow"), ("dog", "bark"), ("cow", "moo")]:
            lx.see(w, [c])
        for w, c in [("cat", "meow"), ("dog", "bark"), ("cow", "moo")]:
            top = lx.meaning(w)
            self.assertEqual(top[0][0], c)
            self.assertAlmostEqual(top[0][1], 1.0, places=2)


class TestPerceptronIntent(unittest.TestCase):
    def test_intent_classification(self):
        p = Perceptron()
        p.train(TRAINING_DATA, epochs=300)
        cases = {
            "hello friend": "greeting",
            "who are you": "identity",
            "how are you": "question",
            "i am sad": "sad",
            "i am happy": "happy",
            "bye bye": "farewell",
            "i have a dog": "statement",
        }
        for text, expected in cases.items():
            label, conf = p.predict(text)
            self.assertEqual(label, expected,
                             f"'{text}' -> {label} (expected {expected})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
