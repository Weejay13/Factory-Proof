import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from factoryproof.runner import FactoryRunner


class RunnerTests(unittest.TestCase):
    def test_demo_run_reaches_human_gate_and_can_be_approved(self):
        with TemporaryDirectory() as directory:
            runner = FactoryRunner(Path(directory), delay=0)
            started = runner.start_run()
            run = self._wait_for(runner, started["id"], {"awaiting_human"})
            self.assertEqual(run["metrics"]["patch_attempts"], 2)
            self.assertEqual(run["metrics"]["blocked_checks"], 1)
            self.assertEqual(run["metrics"]["sealed_tests"], "pass")
            self.assertEqual(run["human_gate"], "pending")
            approved = runner.approve(run["id"])
            self.assertEqual(approved["status"], "shipped")
            self.assertEqual(approved["human_gate"], "approved")
            self.assertEqual(approved["report"]["recommendation"], "promote")

    def test_approve_is_rejected_before_gate(self):
        with TemporaryDirectory() as directory:
            runner = FactoryRunner(Path(directory), delay=0)
            run = runner.start_run()
            result = runner.approve(run["id"])
            self.assertNotEqual(result["status"], "shipped")

    @staticmethod
    def _wait_for(runner, run_id, statuses):
        deadline = time.time() + 10
        while time.time() < deadline:
            current = runner.get_run(run_id)
            if current and current["status"] in statuses:
                return current
            time.sleep(0.01)
        raise AssertionError(f"run did not reach {statuses}")


if __name__ == "__main__":
    unittest.main()
