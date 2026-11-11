"""
NSM 1.2 Adversarial Test Suite.
These tests are designed to break the current system. 
Failure is EXPECTED in v1.1. Passing is the goal for v1.2.
"""
import unittest
import time
from src.brain import Brain

class TestDefeasibleReasoning(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)
        # Default reasoning setup
        self.b.observe("Bird can fly")
        self.b.observe("Penguin is Bird")
        
    def test_penguin_exception(self):
        """A penguin is a bird, but penguins cannot fly (Exception handling)."""
        # If we don't explicitly tell it, it shouldn't hallucinate that penguin flies.
        # Or if we teach it NOT to fly, it should override the Bird rule.
        self.b.observe("Penguin can not fly")
        
        # Ask: Can penguin fly?
        r = self.b.observe("Can penguin fly")
        # Expected in 1.2: "No, penguin can not fly"
        # Current 1.1 behavior: "Yes, because penguin is bird and bird can fly" (FAIL)
        self.assertIn("No", r["response"])

class TestContradictionHandling(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_color_contradiction(self):
        """Sky is green -> Sky is blue. Both facts must be retained (no silent loss)."""
        self.b.observe("Sky is green")
        self.b.observe("Sky is blue")
        
        # Both facts must be in the relation history (no data loss)
        history = self.b.relations.history("IS", "sky")
        self.assertIn("green", history, "Green fact was lost!")
        self.assertIn("blue", history, "Blue fact was lost!")

class TestCycleDetection(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_infinite_loop(self):
        """A IS B -> B IS A. Reasoner should not infinite-loop."""
        self.b.observe("A is B")
        self.b.observe("B is A")
        
        # Should not crash or hang
        start = time.time()
        r = self.b.observe("Is A B?")
        elapsed = time.time() - start
        self.assertLess(elapsed, 2.0, "Reasoner hung on cycle!")

class TestForgetDerivedFacts(unittest.TestCase):
    def setUp(self):
        self.b = Brain(auto_save_path=None)

    def test_forget_parent_purges_child(self):
        """If Dog IS Animal is forgotten, Dog CAN breathe must also vanish."""
        self.b.observe("Dog is Animal")
        self.b.observe("Animal can breathe")
        
        # Check derived fact exists
        r1 = self.b.observe("Can dog breathe")
        self.assertIn("Yes", r1["response"])
        
        # Now forget the parent
        self.b.observe("Forget animal")
        
        # Derived fact should also be gone (currently it will still say YES due to cache/graph)
        r2 = self.b.observe("Can dog breathe")
        lower_resp = r2["response"].lower()
        self.assertTrue("don't know" in lower_resp or "don't have" in lower_resp, f"Got: {r2['response']}")

class TestScaleAndCapacity(unittest.TestCase):
    def test_1000_facts_latency(self):
        """Insert 1000 facts and ensure retrieval doesn't slow down to a halt."""
        b = Brain(auto_save_path=None)
        start = time.time()
        for i in range(1000):
            b.observe(f"Thing{i} is Entity{i}")
        
        insert_time = time.time() - start
        
        # Query
        start_q = time.time()
        r = b.observe("What is Thing500")
        query_time = time.time() - start_q
        
        print(f"\n[SCALE TEST] Insert 1000 facts: {insert_time:.2f}s | Query: {query_time:.2f}s")
        self.assertLess(query_time, 1.0, "Query too slow for 1000 facts!")

if __name__ == "__main__":
    unittest.main()
