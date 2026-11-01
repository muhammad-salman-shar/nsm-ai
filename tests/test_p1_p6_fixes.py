"""Regression tests for P1-P5 fixes."""
import unittest
from src.brain import Brain, _is_question_text

class TestQuestionClassification(unittest.TestCase):
    def test_direct_question_with_qmark(self):
        self.assertTrue(_is_question_text("What is NSM VB?"))
    def test_direct_question_no_qmark(self):
        self.assertTrue(_is_question_text("What is NSM VB"))
    def test_indirect_question_prefix(self):
        self.assertTrue(_is_question_text("So what is nsm vb"))
    def test_statement_with_wh_word(self):
        self.assertFalse(_is_question_text("I know what this is"))
    def test_statement_yes_is_query(self):
        self.assertFalse(_is_question_text("yes is a query"))
    def test_plain_statement(self):
        self.assertFalse(_is_question_text("Hello there"))
    def test_aux_verb_question(self):
        self.assertTrue(_is_question_text("Are you free"))
    def test_pronoun_i_statement(self):
        self.assertFalse(_is_question_text("I am salman"))

class TestPronounBlocklist(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)
    def test_you_not_stored_as_definition(self):
        self.b.observe("Yes you are completely free and open source")
        self.assertNotIn("you", self.b.definitions)
    def test_they_not_stored_as_definition(self):
        self.b.observe("They are very happy")
        self.assertNotIn("they", self.b.definitions)
    def test_i_still_works(self):
        # "I" must still work in fact extraction
        self.b.observe("I am Salman")
        self.assertEqual(self.b.fact_store.get("name"), "Salman")

class TestForgetScope(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)
    def test_forget_marks_episodes_rejected(self):
        self.b.observe("Pakistan is a country in Asia")
        self.b.observe("Forget pakistan")
        # Exclude the "Forget pakistan" command itself from the check
        pak_episodes = [ep for ep in self.b.episodic.episodes
                        if "pakistan" in ep.get("text", "").lower() and "forget" not in ep.get("text", "").lower()]
        self.assertTrue(len(pak_episodes) > 0)
        for ep in pak_episodes:
            self.assertEqual(ep.get("feedback"), "rejected", f"Episode {ep['text']!r} not marked rejected")

    def test_forget_marks_qa_pairs_rejected(self):
        self.b.observe("When I say foobar, reply bazqux")
        self.b.observe("Forget foobar")
        matching = [qa for qa in self.b.qa_pairs if "foobar" in qa.get("pattern", "").lower()]
        self.assertTrue(len(matching) > 0)
        for qa in matching:
            self.assertTrue(qa.get("rejected"))

    def test_forget_hides_from_recall(self):
        self.b.observe("Zanzibar is an island")
        self.b.observe("Forget zanzibar")
        matches = self.b.episodic.recall("tell me about zanzibar", top_k=3)
        for ep, _score in matches:
            self.assertNotEqual(ep.get("feedback"), "rejected")

class TestInstructionRegex(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)
    def test_if_i_say(self):
        r = self.b.observe("When I say hello, reply hi there friend")
        self.assertIn("Rule saved", r["response"])
        self.assertEqual(len(self.b.qa_pairs), 1)
    def test_if_someone_ask(self):
        r = self.b.observe("If someone ask are you free then say yes")
        self.assertIn("Rule saved", r["response"])
        self.assertEqual(len(self.b.qa_pairs), 1)
        self.assertEqual(self.b.qa_pairs[0]["answer"], "yes")
    def test_lookup_after_teach(self):
        self.b.observe("If someone ask are you free then say yes")
        r = self.b.observe("Are you free?")
        self.assertEqual(r["response"], "yes")
    def test_rejected_qa_skipped(self):
        self.b.observe("When I say foobar, reply bazqux")
        self.b.observe("Forget foobar")
        result = self.b._lookup_qa_response("foobar")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
