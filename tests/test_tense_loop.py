import unittest
from src.parser_v2 import parse_to_meaning
from src.realizer import realize

class TestTenseLoop(unittest.TestCase):
    def test_past_loop(self):
        meaning = parse_to_meaning("salman ate mango")
        self.assertEqual(meaning[4], "past")
        self.assertEqual(realize(meaning), "Salman ate mango.")

    def test_present_loop(self):
        meaning = parse_to_meaning("salman eats mango")
        self.assertEqual(meaning[4], "present")
        self.assertEqual(realize(meaning), "Salman eats mango.")

    def test_future_loop(self):
        meaning = parse_to_meaning("salman will eat mango")
        self.assertEqual(meaning[4], "future")
        self.assertEqual(realize(meaning), "Salman will eat mango.")

    def test_irregular_past(self):
        meaning = ("SVO", "salman", "eat", "mango", "past")
        self.assertEqual(realize(meaning), "Salman ate mango.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
