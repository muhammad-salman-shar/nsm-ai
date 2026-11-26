"""End-to-end Pure-English conversational intelligence test suite for NSM VB v1.5."""

import unittest

from src import storage
from src.brain import Brain


class TestNSMv15Conversation(unittest.TestCase):
    def setUp(self):
        self.brain = Brain(seed_core=True)

    def test_causal_consequence_purpose_how_and_parts(self):
        self.brain.observe_bulk(
            "Overheating causes CPU throttling. "
            "If power is turned off, RAM loses its data. "
            "A compiler works by translating source code into machine code. "
            "RAM is used for storing active programs. "
            "CPU consists of ALU, control unit, and registers."
        )

        r_cause = self.brain.observe_bulk("What causes CPU throttling?")
        self.assertEqual(r_cause["mode"], "stored")
        self.assertIn("overheating", r_cause["response"].lower())

        r_if = self.brain.observe_bulk("What happens if power is turned off?")
        self.assertEqual(r_if["mode"], "stored")
        self.assertIn("ram loses its data", r_if["response"].lower())

        r_how = self.brain.observe_bulk("How does a compiler work?")
        self.assertEqual(r_how["mode"], "stored")
        self.assertIn("translating source code", r_how["response"].lower())

        r_use = self.brain.observe_bulk("Hey bro, can you tell me what is RAM used for?")
        self.assertEqual(r_use["mode"], "stored")
        self.assertIn("storing active programs", r_use["response"].lower())

        r_parts = self.brain.observe_bulk("What are the parts of CPU?")
        self.assertEqual(r_parts["mode"], "stored")
        self.assertIn("alu", r_parts["response"].lower())

    def test_compare_dedup_choice_examples_verify_and_coreference(self):
        self.brain.observe_bulk("Hash table is a data structure. Graph is a data structure.")
        self.brain.observe_bulk("SSD is faster than HDD.")
        self.brain.observe_bulk("CPU is also known as Central Processing Unit. CPU is used for executing instructions.")
        self.brain.observe_bulk("Penguin is a bird. Penguin is not a fish.")

        # Comparison must NEVER duplicate the same sentence
        r_cmp = self.brain.observe_bulk("What is the difference between SSD and HDD?")
        self.assertEqual(r_cmp["mode"], "stored")
        self.assertEqual(r_cmp["response"].lower().count("ssd is faster than hdd"), 1)

        # Choice
        r_ch = self.brain.observe_bulk("Is penguin a bird or a fish?")
        self.assertEqual(r_ch["mode"], "stored")
        self.assertIn("bird", r_ch["response"].lower())
        self.assertIn("not a fish", r_ch["response"].lower())

        # Examples
        r_ex = self.brain.observe_bulk("Give me examples of data structure")
        self.assertEqual(r_ex["mode"], "stored")
        self.assertIn("hash table", r_ex["response"].lower())
        self.assertIn("graph", r_ex["response"].lower())

        # Alias + active-topic coreference follow-up
        r_aka = self.brain.observe_bulk("What else is CPU called?")
        self.assertEqual(r_aka["mode"], "stored")
        self.assertIn("central processing unit", r_aka["response"].lower())

        r_coref = self.brain.observe_bulk("What is it used for?")
        self.assertEqual(r_coref["mode"], "stored")
        self.assertIn("executing instructions", r_coref["response"].lower())

        # Polar verification (Yes/No)
        r_ver = self.brain.observe_bulk("Is hash table a data structure?")
        self.assertEqual(r_ver["mode"], "stored")
        self.assertIn("yes", r_ver["response"].lower())

    def test_v15_portable_contract_export_merge_and_custom_patterns(self):
        self.brain.skills["installed"]["demo_skill"] = {"name": "demo_skill", "version": "1.0"}
        self.brain.language_extensions["custom_patterns"].append({
            "id": "custom_scoop_en",
            "kind": "question",
            "qtype": "QUERY_DEFINE",
            "pattern": r"^give\s+me\s+the\s+scoop\s+on\s+(.+)$",
            "slots": {"subject": 1},
            "meta": {"relation": "DEFINED_AS"},
        })
        self.brain.observe_bulk("SQLite is a lightweight embedded database.")

        exported = self.brain.to_dict()
        ok, _ = storage.validate_brain_file(exported)
        self.assertTrue(ok)
        self.assertEqual(exported["nsm_version"], "1.5")
        self.assertEqual(exported["package_type"], "brain")

        restored = Brain.from_dict(exported)
        self.assertIn("demo_skill", restored.skills["installed"])
        res = restored.observe_bulk("Give me the scoop on SQLite")
        self.assertEqual(res["mode"], "stored")
        self.assertIn("embedded database", res["response"].lower())


if __name__ == "__main__":
    unittest.main()
