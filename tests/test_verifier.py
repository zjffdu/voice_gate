import unittest

import numpy as np

from voice_gate.verifier import get_similarity_ranking, verify_voice


class TestVerifier(unittest.TestCase):
    def test_verify_voice_returns_none_when_database_empty(self):
        result = verify_voice(np.array([1.0, 0.0], dtype=np.float32), {})
        self.assertIsNone(result)

    def test_verify_voice_identifies_best_match(self):
        db = {
            "alice": {
                "embedding": np.array([1.0, 0.0], dtype=np.float32)
            },
            "bob": {
                "embedding": np.array([0.0, 1.0], dtype=np.float32)
            },
        }

        probe = np.array([0.9, 0.1], dtype=np.float32)
        result = verify_voice(probe, db, threshold=0.5)

        self.assertEqual(result["matched_user"], "alice")
        self.assertGreater(result["similarity"], 0.5)
        self.assertTrue(result["passed"])
        self.assertIn("all_similarities", result)

    def test_verify_voice_respects_threshold(self):
        db = {
            "alice": {
                "embedding": np.array([1.0, 0.0], dtype=np.float32)
            }
        }

        probe = np.array([0.7, 0.3], dtype=np.float32)
        result = verify_voice(probe, db, threshold=0.95)

        self.assertEqual(result["matched_user"], "alice")
        self.assertFalse(result["passed"])

    def test_get_similarity_ranking_orders_descending(self):
        similarities = {
            "alice": 0.9,
            "bob": 0.6,
            "charlie": 0.3,
        }

        ranking = get_similarity_ranking(similarities, threshold=0.5)

        self.assertEqual([entry["user_id"] for entry in ranking], ["alice", "bob", "charlie"])
        self.assertTrue(ranking[0]["passed"])
        self.assertFalse(ranking[-1]["passed"])


if __name__ == "__main__":
    unittest.main()
