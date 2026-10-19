import unittest
from src.relations import RelationStore
from src.reasoner import infer_relation

class TestReasoner(unittest.TestCase):
    def setUp(self):
        self.rs = RelationStore()
        # salman is human, human is mortal
        self.rs.add("IS", "salman", "human")
        self.rs.add("IS", "human", "mortal")

    def test_direct_inference(self):
        success, msg = infer_relation(self.rs, "salman", "IS", "human")
        self.assertTrue(success)

    def test_infer_relation(self):
        success, msg = infer_relation(self.rs, "salman", "IS", "mortal")
        self.assertTrue(success)
        self.assertIn("because salman is human and human is mortal", msg)

    def test_failed_inference(self):
        success, msg = infer_relation(self.rs, "salman", "IS", "bird")
        self.assertFalse(success)

if __name__ == "__main__":
    unittest.main(verbosity=2)
