import unittest
from src.brain import Brain
from src.parser_v2 import parse_to_meaning
from src.realizer import realize

class TestConstructionBroaden(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_loop_negation(self):
        meaning = parse_to_meaning("tiger is not a bird")
        self.assertEqual(meaning, ("NOT_IS_A", "tiger", "bird"))
        self.assertEqual(realize(meaning), "Tiger is not a bird.")

    def test_loop_question(self):
        meaning = parse_to_meaning("is tiger a mammal")
        self.assertEqual(meaning, ("Q_IS_A", "tiger", "mammal"))
        self.assertEqual(realize(meaning), "Is tiger a mammal?")

    def test_brain_question_yes(self):
        self.b.observe("tiger is a mammal")
        r = self.b.observe("is tiger a mammal")
        self.assertEqual(r["response"], "Yes, tiger is a mammal.")

    def test_brain_question_no(self):
        self.b.observe("tiger is a mammal")
        r = self.b.observe("is tiger a bird")
        # Honest behavior: knows tiger is mammal, but unsure about bird
        self.assertIn("tiger is mammal", r["response"].lower())
        self.assertIn("don't know", r["response"].lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
