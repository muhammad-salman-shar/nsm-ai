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


    def test_capability_boundary_and_compound_topic(self):
        self.brain.observe_bulk("CPU can execute binary machine instructions.")
        self.brain.observe_bulk("SQLite is a serverless database.")
        self.brain.observe_bulk("Hash table is a data structure. Hash table is a key-value structure.")

        # Boundary test: must stay unknown for SQLite, never falsely claim STORED from CPU
        res_bound = self.brain.observe_bulk("Can SQLite execute binary machine instructions?")
        self.assertEqual(res_bound["mode"], "unknown")
        self.assertIn("no stored evidence", res_bound["response"].lower())

        # Compound topic test: must retrieve BOTH frames for hash table
        res_comp = self.brain.observe_bulk("What is a hash table and what is it a type of?")
        self.assertEqual(res_comp["mode"], "stored")
        self.assertIn("data structure", res_comp["response"].lower())
        self.assertIn("key-value", res_comp["response"].lower())


    def test_leadin_question_and_noise_rejection(self):
        # "Ok what is science" must be treated as a question, NEVER stored as "Ok What is science"
        res_q = self.brain.observe_bulk("Ok what is science")
        self.assertEqual(res_q["mode"], "unknown")
        self.assertNotIn("ok what", self.brain.hypergraph._by_agent)

        # Teach science + branches + compound entity
        self.brain.observe_bulk("Science is a systematic discipline.")
        self.brain.observe_bulk("Remember this There are many branches of science, most popular are biology chemistry physics and mathematics.")
        self.brain.observe_bulk("Human brain is the central organ of the nervous system.")

        # Unknown topics must stay unknown (zero noise bleed)
        res_unk = self.brain.observe_bulk("What is animal?")
        self.assertEqual(res_unk["mode"], "unknown")

        # Branches query must return branches, not generic definition
        res_br = self.brain.observe_bulk("What are branches of science?")
        self.assertIn("biology", res_br["response"].lower())

        # Partial entity query "What is brain" must find "Human Brain"
        res_brain = self.brain.observe_bulk("What is brain?")
        self.assertIn("nervous system", res_brain["response"].lower())


if __name__ == "__main__":
    unittest.main()
