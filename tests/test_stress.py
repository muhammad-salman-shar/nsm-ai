"""Core verification suite for NSM VB v1.4 cognitive architecture."""

import unittest

from src.brain import Brain
from src import storage


class TestNSMv14Core(unittest.TestCase):
    def setUp(self):
        self.brain = Brain(seed_core=True)

    def test_core_neurasamu_identity(self):
        res = self.brain.observe_bulk("Who created you?")
        self.assertIn("Muhammad Salman Shar", res["response"])
        self.assertEqual(res["mode"], "stored")

    def test_role_binding_dog_bit_man(self):
        self.brain.observe_bulk("A dog bit a man.")
        res_who = self.brain.observe_bulk("Who bit the man?")
        self.assertIn("Dog", res_who["response"])
        res_what = self.brain.observe_bulk("Who did the dog bite?")
        self.assertIn("man", res_what["response"].lower())

    def test_defeasible_inheritance_penguin(self):
        self.brain.observe_bulk("Bird can fly. Penguin is a bird. Penguin cannot fly.")
        res = self.brain.observe_bulk("Can penguin fly?")
        self.assertIn("cannot fly", res["response"].lower())
        self.assertEqual(res["mode"], "stored")

        self.brain.observe_bulk("Sparrow is a bird.")
        res2 = self.brain.observe_bulk("Can sparrow fly?")
        self.assertIn("can fly", res2["response"].lower())
        self.assertEqual(res2["mode"], "derived")

    def test_surgical_credit_assignment_and_meta_recall(self):
        self.brain.observe_bulk("Mars is a planet.")
        ans = self.brain.observe_bulk("What is Mars?")
        self.assertTrue(len(ans["recalled_frame_ids"]) > 0)
        fid = ans["recalled_frame_ids"][0]
        before = self.brain.hypergraph.bayesian_confidence(self.brain.hypergraph.frames[fid])
        fb = self.brain.apply_feedback(positive=False, episode_id=ans["episode_id"])
        self.assertTrue(fb["ok"])
        after = self.brain.hypergraph.bayesian_confidence(self.brain.hypergraph.frames[fid])
        self.assertLess(after, before)

        meta = self.brain.observe_bulk("What did you recall last time?")
        self.assertIn("Mars", meta["response"])

    def test_sleep_consolidation_and_export_import(self):
        self.brain.observe_bulk("Python is a programming language.")
        self.brain.observe_bulk("What is Python?")
        self.brain.observe_bulk("What is Python?")
        rep = self.brain.run_sleep_consolidation(force=True)
        self.assertGreaterEqual(rep["total_schemas"], 1)

        exported = self.brain.to_dict()
        ok, _ = storage.validate_brain_file(exported)
        self.assertTrue(ok)
        restored = Brain.from_dict(exported)
        res = restored.observe_bulk("What is Python?")
        self.assertIn("programming language", res["response"].lower())


if __name__ == "__main__":
    unittest.main()
