import unittest

from app import Store


class StageFourTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.create_wallet({"user_id": "alice", "balance_cents": 1000})
        self.store.create_wallet({"user_id": "bob", "balance_cents": 0})
        self.transfer = self.store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 250, "idempotency_key": "pay-1"})

    def test_refund_is_idempotent_and_reverses_once(self):
        first = self.store.refund(self.transfer["transfer_id"], {"idempotency_key": "refund-1"})
        second = self.store.refund(self.transfer["transfer_id"], {"idempotency_key": "refund-1"})
        self.assertEqual(first, second)
        self.assertEqual(self.store.wallets["alice"]["balance_cents"], 1000)
        self.assertEqual(self.store.wallets["bob"]["balance_cents"], 0)

    def test_transfer_cannot_be_refunded_twice_with_different_keys(self):
        self.store.refund(self.transfer["transfer_id"], {"idempotency_key": "refund-1"})
        with self.assertRaises(ValueError):
            self.store.refund(self.transfer["transfer_id"], {"idempotency_key": "refund-2"})


if __name__ == "__main__":
    unittest.main()
