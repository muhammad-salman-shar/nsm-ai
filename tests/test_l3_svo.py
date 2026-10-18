import unittest
from src.brain import Brain
from src.producer import produce_svo
from src.relations import extract, parse_query

class TestPatterns(unittest.TestCase):
    def test_conjugation(self):
        self.assertEqual(produce_svo("salman", "like", "mangoes"), "Salman likes mangoes.")
        self.assertEqual(produce_svo("i", "like", "mangoes"), "I like mangoes.")
        self.assertEqual(produce_svo("they", "play", "football"), "They play football.")

class TestRelationsSVO(unittest.TestCase):
    def test_extract_svo(self):
        rels = extract("salman", "salman likes mangoes")
        self.assertTrue(any(r["type"] == "LIKE" and r["object"] == "mangoes" for r in rels))
        
    def test_parse_svo_query(self):
        self.assertEqual(parse_query("what does salman like"), ("SVO", "salman", "like"))

class TestBrainL3(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_learn_and_query_svo(self):
        self.b.observe("salman likes mangoes")
        r = self.b.observe("what does salman like")
        self.assertEqual(r["response"], "Salman likes mangoes.")

    def test_query_unknown_svo(self):
        r = self.b.observe("what does salman want")
        self.assertIn("I don't know what salman wants.", r["response"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
