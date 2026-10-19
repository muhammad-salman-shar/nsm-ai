import unittest
from src.parser_v2 import parse_to_meaning
from src.realizer import realize

class TestPronounBeVerb(unittest.TestCase):
    def test_i_am(self):
        meaning = parse_to_meaning("i am an animal")
        self.assertEqual(realize(meaning), "I am an animal.")

    def test_he_is(self):
        meaning = parse_to_meaning("he is a doctor")
        self.assertEqual(realize(meaning), "He is a doctor.")

    def test_normalize_me(self):
        meaning = parse_to_meaning("me am happy")
        # Should normalize "me" to "i"
        self.assertEqual(meaning[1], "i")

if __name__ == "__main__":
    unittest.main(verbosity=2)
