import unittest
from src.parser_v2 import parse_to_meaning
from src.realizer import realize

class TestGrammarMonster(unittest.TestCase):
    def test_negation(self):
        meaning = parse_to_meaning("salman does not eat mango")
        self.assertEqual(meaning[0], "NOT_SVO")
        self.assertEqual(realize(meaning), "Salman does not eat mango.")

    def test_wh_question(self):
        meaning = parse_to_meaning("what does salman eat")
        self.assertEqual(meaning[0], "SVO_QUERY")
        self.assertEqual(realize(meaning), "What does salman eat?")

    def test_yes_no_question(self):
        meaning = parse_to_meaning("does salman eat mango")
        self.assertEqual(meaning[0], "SVO_YESNO")
        self.assertEqual(realize(meaning), "Does salman eat mango?")

if __name__ == "__main__":
    unittest.main(verbosity=2)
