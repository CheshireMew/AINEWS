
import sys
import os
import unittest
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler.filters.local_deduplicator import LocalDeduplicator

class TestRefactoredDeduplicator(unittest.TestCase):
    def setUp(self):
        self.dedup = LocalDeduplicator(similarity_threshold=0.6, time_window_hours=24)

    def test_basic_dedup(self):
        news = [
            {"id": 1, "title": "Bitcoin surges to 50k", "published_at": "2025-01-01T10:00:00Z"},
            {"id": 2, "title": "Bitcoin hits 50,000 dollars", "published_at": "2025-01-01T09:00:00Z"},
        ]
        res = self.dedup.mark_duplicates(news)
        # ID 1 (Newer) should be dup of ID 2 (Older)
        if not res[0]['is_local_duplicate']:
            f1 = self.dedup.extract_key_features(news[0]['title'])
            f2 = self.dedup.extract_key_features(news[1]['title'])
            sim = self.dedup.calculate_similarity_from_features(f1, f2)
            print(f"\n[FAIL] Basic Dedup Sim: {sim}")
            print(f"F1 Num: {f1['numbers']}")
            print(f"F2 Num: {f2['numbers']}")
            print(f"F1 KW: {f1['keywords']}")
            print(f"F2 KW: {f2['keywords']}")
            
        self.assertTrue(res[0]['is_local_duplicate'])
        self.assertEqual(res[0]['duplicate_of'], 2)
        self.assertFalse(res[1]['is_local_duplicate'])

    def test_year_filtering_preserves_price(self):
        # 1800 should be treated as a number (price), not a year
        news = [
            {"id": 1, "title": "Gold hits 1800", "published_at": "2025-01-01T10:00:00Z"},
            {"id": 2, "title": "Gold hits 1805", "published_at": "2025-01-01T09:00:00Z"}, # Similar price
            {"id": 3, "title": "Gold hits 2024", "published_at": "2025-01-01T08:00:00Z"}  # 2024 might be year or price
        ]
        
        # 1800 vs 1805 should match (close numbers)
        # Sim(1, 2)
        f1 = self.dedup.extract_key_features(news[0]['title'])
        f2 = self.dedup.extract_key_features(news[1]['title'])
        # 1800 and 1805 should be in 'numbers'
        self.assertIn('1800', f1['numbers'])
        self.assertIn('1805', f2['numbers'])
        
        sim = self.dedup.calculate_similarity_from_features(f1, f2)
        print(f"Sim 1800 vs 1805: {sim}")
        self.assertGreater(sim, 0.6)

    def test_time_window(self):
        # Window is 24h
        news = [
            {"id": 1, "title": "Same Title", "published_at": "2025-01-02T10:00:00Z"},
            {"id": 2, "title": "Same Title", "published_at": "2025-01-01T05:00:00Z"}, # > 24h diff (29h)
        ]
        res = self.dedup.mark_duplicates(news)
        self.assertFalse(res[0]['is_local_duplicate'], "Should not dedup outside window")

    def test_chain_resolution(self):
        # A(New) -> B(Old) -> C(Oldest)
        news = [
            {"id": 1, "title": "Bitcoin updates 1", "published_at": "2025-01-01T12:00:00Z"},
            {"id": 2, "title": "Bitcoin updates 1", "published_at": "2025-01-01T11:00:00Z"},
            {"id": 3, "title": "Bitcoin updates 1", "published_at": "2025-01-01T10:00:00Z"},
        ]
        res = self.dedup.mark_duplicates(news)
        
        # ID 3 is Master
        self.assertFalse(res[2]['is_local_duplicate'])
        
        # ID 2 dup of 3
        self.assertEqual(res[1]['duplicate_of'], 3)
        
        # ID 1 dup of 3 (Flattened) or 2?
        # Ideally 3 if transitivity works
        # Since they are identical, Sim(1,3) is high, so it should resolve to 3.
        print(f"ID 1 dup of: {res[0]['duplicate_of']}")
        self.assertEqual(res[0]['duplicate_of'], 3)

if __name__ == '__main__':
    import sys
    with open('verification_result.log', 'w') as f:
        sys.stdout = f
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestRefactoredDeduplicator)
        result = runner.run(suite)
        sys.stdout = sys.__stdout__ # Restore
        
    if result.wasSuccessful():
        print("SUCCESS")
        exit(0)
    else:
        print("FAILURE")
        exit(1)
