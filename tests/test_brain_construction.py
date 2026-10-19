import unittest
from src.brain import Brain

class TestBrainConstruction(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_learn_then_query_is_a(self):
        self.b.observe("tiger is a mammal")
        r = self.b.observe("what is tiger")
        self.assertEqual(r["response"], "Tiger is a mammal.")

    def test_learn_then_query_is_a_an(self):
        self.b.observe("eagle is an animal")
        r = self.b.observe("what is eagle")
        self.assertEqual(r["response"], "Eagle is an animal.")

    def test_learn_then_query_is_prop(self):
        self.b.observe("mango is sweet")
        r = self.b.observe("what is mango")
        self.assertEqual(r["response"], "Mango is sweet.")

    def test_generalization_unseen_subject(self):
        # Even though tiger was never taught here, if meaning exists it should work
        self.b.meanings["lion"] = ("IS_A", "lion", "animal")
        r = self.b.observe("what is lion")
        self.assertEqual(r["response"], "Lion is an animal.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
