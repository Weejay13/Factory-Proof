import unittest

from factoryproof.acceptance import demo_sources, make_patch, verify_candidate


class AcceptanceTests(unittest.TestCase):
    def test_first_candidate_passes_public_but_not_sealed_checks(self):
        result = verify_candidate(demo_sources()["v1"])
        self.assertTrue(result["public"]["passed"])
        self.assertFalse(result["sealed"]["passed"])

    def test_revised_candidate_passes_both_suites(self):
        result = verify_candidate(demo_sources()["v2"])
        self.assertTrue(result["public"]["passed"])
        self.assertTrue(result["sealed"]["passed"])

    def test_patch_contains_the_idempotency_guard(self):
        patch = make_patch(demo_sources()["v1"], demo_sources()["v2"])
        self.assertIn("if idempotency_key in self._by_key", patch)
        self.assertIn("return self._by_key[idempotency_key]", patch)
