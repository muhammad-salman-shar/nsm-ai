import unittest
from src.parser_v2 import parse_to_meaning
from src.realizer import realize

class TestConstructionLoop(unittest.TestCase):
    def test_is_a_loop(self):
        text = "salman is a human"
        meaning = parse_to_meaning(text)
        self.assertEqual(meaning, ("IS_A", "salman", "human"))
        
        out = realize(meaning)
        self.assertEqual(out, "Salman is a human.")

    def test_is_prop_loop(self):
        text = "mango is sweet"
        meaning = parse_to_meaning(text)
        self.assertEqual(meaning, ("IS_PROP", "mango", "sweet"))
        
        out = realize(meaning)
        self.assertEqual(out, "Mango is sweet.")

    def test_svo_loop(self):
        text = "salman likes mango"
        meaning = parse_to_meaning(text)
        self.assertEqual(meaning, ("SVO", "salman", "likes", "mango"))
        
        out = realize(meaning)
        self.assertEqual(out, "Salman likes mango.")

    def test_unseen_generalization(self):
        # Bahar se naya meaning aaya, bot ne khud sentence banaya
        meaning = ("IS_A", "tiger", "animal")
        out = realize(meaning)
        self.assertEqual(out, "Tiger is an animal.") # Notice the 'an' logic!

if __name__ == "__main__":
    unittest.main(verbosity=2)
