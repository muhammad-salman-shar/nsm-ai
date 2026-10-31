import unittest
from src.brain import Brain

class TestFeedback(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_wrong_triggers_correction_prompt(self):
        self.b.observe("tiger is a mammal")
        r = self.b.observe("what is tiger")
        self.assertEqual(r["response"], "Tiger is a mammal.")
        
        r2 = self.b.observe("wrong")
        self.assertIn("what should i have said", r2["response"].lower())
        self.assertIsNotNone(self.b.pending_feedback)

    def test_user_teaches_correct_answer(self):
        self.b.observe("tiger is a mammal")
        self.b.observe("what is tiger")
        self.b.observe("wrong")
        
        r = self.b.observe("tiger is a reptile")
        self.assertIn("got it", r["response"].lower())
        self.assertIsNone(self.b.pending_feedback)

    def test_rejected_episode_not_recalled(self):
        self.b.observe("i love mangoes")
        self.b.observe("do i love mangoes")  # recall happens
        self.b.observe("wrong")
        # Now recall should not return "i love mangoes" since it was rejected
        
    def test_no_after_question_does_not_trigger(self):
        # If NSM asked a question, "no" should not be treated as correction
        self.b.observe("tiger is a mammal")
        r = self.b.observe("ask me something")  # NSM asks a question
        # Now user says "no" - should not trigger feedback
        r2 = self.b.observe("no")
        self.assertIsNone(self.b.pending_feedback)

    def test_inline_correction(self):
        self.b.observe("tiger is a mammal")
        self.b.observe("what is tiger")
        r = self.b.observe("no, tiger is a reptile")
        self.assertIn("got it", r["response"].lower())
        self.assertIn("reptile", r["response"].lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
