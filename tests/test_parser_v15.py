"""Comprehensive Pure-English verification suite for NSM VB v1.5 Compositional Parser."""

import unittest

from src.parser import CompositionalParser


class TestCompositionalParserV15(unittest.TestCase):
    def setUp(self):
        self.parser = CompositionalParser()

    def test_all_16_question_types_english(self):
        cases = [
            # 1. Definition
            ("What is an algorithm?", "QUERY_DEFINE", "algorithm"),
            ("What does CPU mean?", "QUERY_DEFINE", "cpu"),
            ("Define compiler", "QUERY_DEFINE", "compiler"),
            # 2. Classification
            ("What kind of structure is a graph?", "QUERY_CLASS", "graph"),
            # 3. Alias / Synonym
            ("What else is CPU called?", "QUERY_ALIAS", "cpu"),
            ("Another name for CPU?", "QUERY_ALIAS", "cpu"),
            # 4. Polar Verification
            ("Is hash table a data structure?", "QUERY_VERIFY", "hash table"),
            ("Does hash table have constant lookup?", "QUERY_VERIFY", "hash table"),
            # 5. Capability
            ("Can RAM retain data?", "QUERY_CAN", "ram"),
            ("Is penguin able to fly?", "QUERY_CAN", "penguin"),
            # 6. Choice / Alternative
            ("Is penguin a bird or a fish?", "QUERY_CHOICE", "penguin"),
            ("Which is faster, SSD or HDD?", "QUERY_CHOICE", ""),
            # 7. Causal
            ("What causes CPU throttling?", "QUERY_CAUSE", "cpu throttling"),
            ("Why does overheating happen?", "QUERY_CAUSE", "overheating happen"),
            # 8. Consequence / Hypothetical
            ("What happens if power is turned off?", "QUERY_IF_THEN", "power is turned off"),
            ("What if memory fills up?", "QUERY_IF_THEN", "memory fills up"),
            # 9. Procedural (How)
            ("How does a compiler work?", "QUERY_HOW", "compiler"),
            # 10. Purpose / Utility
            ("What is RAM used for?", "QUERY_PURPOSE", "ram"),
            ("What is the purpose of SQLite?", "QUERY_PURPOSE", "sqlite"),
            # 11. Composition / Parts
            ("What are the parts of CPU?", "QUERY_PARTS", "cpu"),
            ("What is computer made of?", "QUERY_PARTS", "computer"),
            # 12. Comparison / Contrast
            ("What is the difference between RAM and ROM?", "QUERY_COMPARE", "ram"),
            ("Compare SSD and HDD", "QUERY_COMPARE", "ssd"),
            # 13. Examples / Instances
            ("Give me examples of data structure", "QUERY_EXAMPLES", "data structure"),
            # 14. Role / Event
            ("Who bit the man?", "QUERY_ROLE", ""),
            ("Who did the dog bite?", "QUERY_ROLE", "dog"),
            # 15. Quantitative / Spatial / Temporal
            ("How many bones does human body have?", "QUERY_FACT_META", "human body"),
            ("Where is SQLite located?", "QUERY_FACT_META", "sqlite"),
            ("When was Python created?", "QUERY_FACT_META", "python"),
            # 16. Follow-up
            ("Tell me more", "QUERY_FOLLOWUP", "cpu"),
            ("Explain simply", "QUERY_FOLLOWUP", "cpu"),
        ]

        for text, expected_qtype, expected_subj in cases:
            with self.subTest(text=text):
                pq = self.parser.parse_question(text, active_topic="cpu")
                self.assertIsNotNone(pq, f"Failed to parse question: {text}")
                self.assertEqual(pq.qtype, expected_qtype, f"Wrong qtype for: {text}")
                if expected_subj:
                    self.assertEqual(pq.subject, expected_subj, f"Wrong subject for: {text}")

    def test_indirect_wrappers_and_coreference(self):
        pq1 = self.parser.parse_question("Hey bro, can you tell me what is RAM used for?")
        self.assertIsNotNone(pq1)
        self.assertEqual(pq1.qtype, "QUERY_PURPOSE")
        self.assertEqual(pq1.subject, "ram")

        pq2 = self.parser.parse_question("Well, do you know the difference between RAM and ROM?")
        self.assertIsNotNone(pq2)
        self.assertEqual(pq2.qtype, "QUERY_COMPARE")
        self.assertEqual(pq2.subject, "ram")
        self.assertEqual(pq2.secondary_subject, "rom")

        pq3 = self.parser.parse_question("How does it work?", active_topic="compiler")
        self.assertIsNotNone(pq3)
        self.assertEqual(pq3.qtype, "QUERY_HOW")
        self.assertEqual(pq3.subject, "compiler")
        self.assertTrue(pq3.coref_resolved)

        pq4 = self.parser.parse_question("What is it used for?", active_topic="sqlite")
        self.assertIsNotNone(pq4)
        self.assertEqual(pq4.qtype, "QUERY_PURPOSE")
        self.assertEqual(pq4.subject, "sqlite")
        self.assertTrue(pq4.coref_resolved)

    def test_all_14_declarative_relations_and_noise_guard(self):
        stmt_cases = [
            ("If power is turned off, RAM loses its data.", "IF_THEN", "power is turned off", 1),
            ("Overheating causes CPU throttling.", "CAUSES", "overheating", 1),
            ("A compiler works by translating source code into machine code.", "WORKS_BY", "compiler", 1),
            ("RAM is used for storing active programs.", "USED_FOR", "ram", 1),
            ("CPU is also known as central processing unit.", "ALSO_KNOWN_AS", "cpu", 1),
            ("A computer is made of hardware and software.", "HAS_PART", "computer", 1),
            ("Remember this There are many branches of science, most popular are biology chemistry physics.", "HAS_BRANCHES", "science", 1),
            ("SSD is faster than HDD.", "COMPARED_TO", "ssd", 1),
            ("Penguin cannot fly.", "CAN", "penguin", -1),
            ("Human skeleton has 206 bones.", "HAS_COUNT", "human skeleton", 1),
            ("Muhammad Salman Shar created NSM VB.", "CREATED", "muhammad salman shar", 1),
            ("SQLite is located in a single disk file.", "LOCATED_IN", "sqlite", 1),
            ("Hash table has constant lookup.", "HAS", "hash table", 1),
            ("Python is a programming language.", "IS_A", "python", 1),
            ("A dog bit a man.", "ACTION", "dog", 1),
        ]

        for text, expected_rel, expected_agent, expected_pol in stmt_cases:
            with self.subTest(text=text):
                ps = self.parser.parse_statement(text)
                self.assertIsNotNone(ps, f"Failed to extract statement: {text}")
                self.assertEqual(ps.relation, expected_rel, f"Wrong relation for: {text}")
                self.assertEqual(ps.agent, expected_agent, f"Wrong agent for: {text}")
                self.assertEqual(ps.polarity, expected_pol, f"Wrong polarity for: {text}")

        self.assertIsNone(self.parser.parse_statement("Ok what is science"))
        self.assertIsNone(self.parser.parse_statement("Hey can you explain science"))

    def test_mixed_turn_and_portable_custom_extensions(self):
        turn = self.parser.parse_turn("A dog bit a man. Who bit the man?")
        self.assertEqual(turn.turn_type, "mixed")
        self.assertEqual(len(turn.statements), 1)
        self.assertEqual(len(turn.questions), 1)
        self.assertEqual(turn.statements[0].agent, "dog")
        self.assertEqual(turn.questions[0].qtype, "QUERY_ROLE")

        count = self.parser.load_custom_patterns([
            {
                "id": "custom_price_en",
                "kind": "question",
                "qtype": "QUERY_FACT_META",
                "pattern": r"^what\s+is\s+the\s+price\s+of\s+(.+)$",
                "slots": {"subject": 1},
                "meta": {"subtype": "price", "relation": "HAS_PRICE"},
            }
        ])
        self.assertEqual(count, 1)
        pq = self.parser.parse_question("What is the price of sugar?")
        self.assertIsNotNone(pq)
        self.assertEqual(pq.subject, "sugar")
        self.assertEqual(pq.meta.get("subtype"), "price")


if __name__ == "__main__":
    unittest.main()
