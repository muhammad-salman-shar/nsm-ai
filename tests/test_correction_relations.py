import unittest
from src.brain import Brain
from src.relations import extract, RelationStore


class TestCorrectionExtraction(unittest.TestCase):
    def test_correct_marker_detected(self):
        rels = extract("zebra", "no zebra is mammal")
        self.assertTrue(rels and rels[0]["correct"])

    def test_actually_marker(self):
        rels = extract("zebra", "actually zebra is mammal")
        self.assertTrue(rels and rels[0]["correct"])

    def test_plain_no_correction(self):
        rels = extract("zebra", "zebra is mammal")
        self.assertFalse(rels and rels[0]["correct"])


class TestContradictionStore(unittest.TestCase):
    def test_accumulate_two_relations(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "bird")
        active = rs.get("IS", "zebra")
        self.assertIn("animal", active)
        self.assertIn("bird", active)

    def test_correction_supersedes(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "mammal", correct=True)
        active = rs.get("IS", "zebra")
        self.assertIn("mammal", active)
        self.assertNotIn("animal", active)
        hist = rs.history("IS", "zebra")
        self.assertTrue(hist["animal"]["superseded"])
        self.assertFalse(hist["mammal"]["superseded"])

    def test_reinforce_count(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "animal")
        hist = rs.history("IS", "zebra")
        self.assertEqual(hist["animal"]["count"], 2)

    def test_query_yes(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        status, _ = rs.query("IS", "zebra", "animal")
        self.assertEqual(status, "yes")

    def test_query_superseded(self):
        rs = RelationStore()
        rs.add("IS", "zebra", "animal")
        rs.add("IS", "zebra", "mammal", correct=True)
        status, _ = rs.query("IS", "zebra", "animal")
        self.assertEqual(status, "superseded")


class TestCorrectionInBrain(unittest.TestCase):
    def test_actually_corrects(self):
        b = Brain()
        b.observe("I saw a zizz")
        b.observe("zizz is animal")
        r1 = b.observe("is zizz an animal")
        self.assertIn("Yes", r1["response"])
        b.observe("actually zizz is mammal")
        r2 = b.observe("is zizz an animal")
        self.assertNotIn("Yes", r2["response"])
        r3 = b.observe("is zizz a mammal")
        self.assertIn("Yes", r3["response"])

    def test_accumulate_without_correction(self):
        b = Brain()
        b.observe("I saw a zizz")
        b.observe("zizz is animal")
        b.observe("zizz is bird")
        r = b.observe("is zizz a bird")
        self.assertIn("Yes", r["response"])

    def test_no_prefix_corrects(self):
        b = Brain()
        b.observe("I saw a zizz")
        b.observe("zizz is animal")
        b.observe("no zizz is mammal")
        r = b.observe("is zizz an animal")
        self.assertNotIn("Yes", r["response"])
        r2 = b.observe("is zizz a mammal")
        self.assertIn("Yes", r2["response"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
