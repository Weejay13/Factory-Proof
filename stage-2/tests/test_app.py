import unittest
from pathlib import Path

from app import Store


class StageTwoTests(unittest.TestCase):
    def test_store_contract(self):
        store = Store()
        store.create_wallet({"user_id": "alice", "balance_cents": 100})
        store.create_wallet({"user_id": "bob", "balance_cents": 0})
        self.assertEqual(store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 25, "idempotency_key": "k1"})["status"], "completed")

    def test_handler_exposes_ui_contract(self):
        source = (Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8")
        self.assertIn("data-testid=\"transfer-status\"", source)


if __name__ == "__main__":
    unittest.main()
