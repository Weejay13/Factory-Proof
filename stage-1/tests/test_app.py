import unittest

from app import Store


class StageOneTests(unittest.TestCase):
    def test_wallet_and_transfer(self):
        store = Store()
        store.create_wallet({"user_id": "alice", "balance_cents": 100})
        store.create_wallet({"user_id": "bob", "balance_cents": 0})
        transfer = store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 25, "idempotency_key": "k1"})
        self.assertEqual(transfer["status"], "completed")
        self.assertEqual(store.wallets["alice"]["balance_cents"], 75)
        self.assertEqual(store.wallets["bob"]["balance_cents"], 25)

    def test_invalid_transfer_is_rejected(self):
        store = Store()
        store.create_wallet({"user_id": "alice", "balance_cents": 1})
        store.create_wallet({"user_id": "bob", "balance_cents": 0})
        with self.assertRaises(ValueError):
            store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 2, "idempotency_key": "k1"})


if __name__ == "__main__":
    unittest.main()
