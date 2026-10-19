import unittest
import os
from src.brain import Brain
from src.llm_teacher import improve_language

class TestTeacherIntegration(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)
        # Ensure no API key is set for tests
        if "NSM_LLM_KEY" in os.environ:
            del os.environ["NSM_LLM_KEY"]

    def test_teacher_fallback(self):
        # Without API key, improve_language should return raw text
        raw = "Tiger ate meat."
        result = improve_language(raw, "what is tiger")
        self.assertEqual(result, raw)

    def test_brain_with_teacher_fallback(self):
        self.b.observe("tiger ate meat")
        r = self.b.observe("what is tiger")
        
        # Response should still be correct via fallback
        self.assertEqual(r["response"], "Tiger ate meat.")
        self.assertEqual(r["raw_thought"], "Tiger ate meat.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
