import unittest
from src.grammar import parse

class TestGrammar(unittest.TestCase):
    def test_i_am_salman(self):
        p = parse("I am Salman")
        self.assertEqual(p["type"], "statement")
        self.assertEqual(p["subject"], ["i"])
        self.assertEqual(p["verb"], ["am"])
        self.assertEqual(p["object"], ["salman"])

    def test_i_like_mangoes(self):
        p = parse("I like mangoes")
        self.assertEqual(p["type"], "statement")
        self.assertEqual(p["subject"], ["i"])
        self.assertEqual(p["verb"], ["like"])
        self.assertEqual(p["object"], ["mangoes"])

    def test_what_is_my_name(self):
        p = parse("What is my name?")
        self.assertEqual(p["type"], "question")
        self.assertEqual(p["qword"], "what")
        self.assertEqual(p["verb"], ["is"])
        self.assertEqual(p["object"], ["my", "name"])

    def test_is_salman_human(self):
        p = parse("Is Salman a human?")
        self.assertEqual(p["type"], "question")
        self.assertEqual(p["aux"], "is")
        self.assertEqual(p["subject"], ["salman"])
        self.assertEqual(p["object"], ["a", "human"])

    def test_do_you_like_mangoes(self):
        p = parse("Do you like mangoes?")
        self.assertEqual(p["type"], "question")
        self.assertEqual(p["aux"], "do")
        self.assertEqual(p["subject"], ["you"])
        self.assertEqual(p["verb"], ["like"])
        self.assertEqual(p["object"], ["mangoes"])

    def test_unknown_sentence(self):
        p = parse("Blah blah zorblax")
        self.assertEqual(p["type"], "statement")
        self.assertEqual(p["subject"], ["blah", "blah", "zorblax"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
