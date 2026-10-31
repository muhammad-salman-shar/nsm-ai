import unittest
import time
import json
from src.brain import Brain
from src import persistence

class TestStress(unittest.TestCase):
    def test_10k_facts(self):
        b = Brain(auto_save_path=None)
        start = time.time()
        for i in range(10000):
            b.fact_store.set(f"fact_{i}", f"value_{i}")
        store_time = time.time() - start
        print(f"\n[STRESS] 10k FACTS store: {store_time:.3f}s")
        
        start = time.time()
        for i in range(1000):
            assert b.fact_store.get(f"fact_{i*10}") == f"value_{i*10}"
        read_time = time.time() - start
        print(f"[STRESS] 1000 FACT reads: {read_time:.3f}s")
        self.assertLess(store_time, 10.0)
        self.assertLess(read_time, 5.0)

    def test_10k_relations(self):
        b = Brain(auto_save_path=None)
        start = time.time()
        for i in range(10000):
            b.relations.add("IS", f"entity_{i}", f"category_{i}")
        store_time = time.time() - start
        print(f"\n[STRESS] 10k RELATIONS store: {store_time:.3f}s")
        
        start = time.time()
        for i in range(1000):
            r = b.relations.get("IS", f"entity_{i*10}")
            assert f"category_{i*10}" in r
        read_time = time.time() - start
        print(f"[STRESS] 1000 RELATION reads: {read_time:.3f}s")
        self.assertLess(store_time, 10.0)
        self.assertLess(read_time, 5.0)

    def test_serialize_10k(self):
        b = Brain(auto_save_path=None)
        for i in range(10000):
            b.fact_store.set(f"fact_{i}", f"value_{i}")
        
        start = time.time()
        data = persistence.to_dict(b)
        ser_time = time.time() - start
        print(f"\n[STRESS] Serialize to_dict(): {ser_time:.3f}s")
        
        json_str = json.dumps(data)
        size_kb = len(json_str) / 1024
        print(f"[STRESS] JSON size: {size_kb:.1f} KB")
        
        b2 = Brain(auto_save_path=None)
        start = time.time()
        persistence.from_dict(b2, data)
        deser_time = time.time() - start
        print(f"[STRESS] Deserialize from_dict(): {deser_time:.3f}s")
        
        self.assertEqual(len(b2.fact_store.facts), 10000)
        self.assertLess(ser_time, 5.0)
        self.assertLess(deser_time, 5.0)

    def test_1L_facts(self):
        """1 Lakh (100k) facts - the real scalability test"""
        b = Brain(auto_save_path=None)
        start = time.time()
        for i in range(100000):
            b.fact_store.set(f"fact_{i}", f"value_{i}")
        store_time = time.time() - start
        print(f"\n[STRESS-100K] 100k FACTS store: {store_time:.3f}s")
        
        start = time.time()
        for i in range(10000):
            assert b.fact_store.get(f"fact_{i*10}") == f"value_{i*10}"
        read_time = time.time() - start
        print(f"[STRESS-100K] 10k FACT reads: {read_time:.3f}s")
        self.assertLess(store_time, 30.0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
