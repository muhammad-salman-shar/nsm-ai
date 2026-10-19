import unittest
from src.parser_v2 import parse_to_meaning
from src.realizer import realize

class TestPluralLoop(unittest.TestCase):
    def test_singular_loop(self):
        meaning = parse_to_meaning("dog is an animal")
        self.assertEqual(realize(meaning), "Dog is an animal.")

    def test_plural_loop(self):
        meaning = parse_to_meaning("dogs are animals")
        self.assertEqual(realize(meaning), "Dogs are animals.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
