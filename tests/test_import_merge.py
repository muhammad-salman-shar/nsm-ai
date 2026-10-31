import unittest
from src import persistence

class TestValidateAndMerge(unittest.TestCase):
    def _valid_brain(self, name="Salman", facts=None):
        return {
            "version": persistence.STATE_VERSION,
            "turn": 1,
            "definitions": {"apple": "a fruit"},
            "relations": {"IS|dog": {"animal": {"count": 1, "first_seen": 0, "last_seen": 0, "superseded": False, "source": "user"}}},
            "lexicon": {"dog": {"count": 1, "contexts": []}},
            "episodes": [{"text": "hello", "mood": "happy"}],
            "facts": facts or {"name": name},
            "affect": {"drives": {}, "hormones": {}}
        }

    def test_validate_valid(self):
        ok, reason = persistence.validate_brain_file(self._valid_brain())
        self.assertTrue(ok, reason)

    def test_validate_invalid_missing_keys(self):
        ok, reason = persistence.validate_brain_file({"version": 1})
        self.assertFalse(ok)
        self.assertIn("Missing required key", reason)

    def test_validate_invalid_version(self):
        data = self._valid_brain()
        data["version"] = 999
        ok, reason = persistence.validate_brain_file(data)
        self.assertFalse(ok)
        self.assertIn("Version mismatch", reason)

    def test_merge_combines_facts(self):
        a = self._valid_brain(facts={"name": "Salman", "age": 25})
        b = self._valid_brain(facts={"name": "Amir", "city": "Karachi"})
        merged = persistence.merge_brain_data(a, b)
        self.assertEqual(merged["facts"]["name"], "Amir")  # Latest wins
        self.assertEqual(merged["facts"]["age"], 25)  # Preserved
        self.assertEqual(merged["facts"]["city"], "Karachi")  # Added

    def test_merge_combines_relations(self):
        a = self._valid_brain()
        b = self._valid_brain()
        b["relations"] = {"IS|cat": {"animal": {"count": 1, "first_seen": 0, "last_seen": 0, "superseded": False, "source": "user"}}}
        merged = persistence.merge_brain_data(a, b)
        self.assertIn("IS|dog", merged["relations"])
        self.assertIn("IS|cat", merged["relations"])

    def test_merge_appends_episodes(self):
        a = self._valid_brain()
        a["episodes"] = [{"text": "first"}]
        b = self._valid_brain()
        b["episodes"] = [{"text": "second"}]
        merged = persistence.merge_brain_data(a, b)
        self.assertEqual(len(merged["episodes"]), 2)

if __name__ == "__main__":
    unittest.main(verbosity=2)
