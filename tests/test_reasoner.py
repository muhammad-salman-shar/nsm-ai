import unittest
from src.relations import RelationStore
from src.reasoner import transitive_inference

class TestReasoner(unittest.TestCase):
    def setUp(self):
        self.rs = RelationStore()
        # salman is human, human is mortal
        self.rs.add("IS", "salman", "human")
        self.rs.add("IS", "human", "mortal")

    def test_direct_inference(self):
        success, msg = transitive_inference(self.rs, "salman", "human")
        self.assertTrue(success)

    def test_transitive_inference(self):
        success, msg = transitive_inference(self.rs, "salman", "mortal")
        self.assertTrue(success)
        self.assertIn("because salman is human and human is mortal", msg)

    def test_failed_inference(self):
        success, msg = transitive_inference(self.rs, "salman", "bird")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main(verbosity=2)
