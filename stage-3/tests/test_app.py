import unittest
from concurrent.futures import ThreadPoolExecutor

from app import Store


class StageThreeTests(unittest.TestCase):
    def setUp(self):
        self.store = Store()
        self.store.create_wallet({"user_id": "alice", "balance_cents": 1000})
        self.store.create_wallet({"user_id": "bob", "balance_cents": 0})

    def test_retry_is_idempotent(self):
        first = self.store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 250, "idempotency_key": "k1"})
        retry = self.store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 250, "idempotency_key": "k1"})
        self.assertEqual(first, retry)
        self.assertEqual(self.store.wallets["alice"]["balance_cents"], 750)
        self.assertEqual(len(self.store.transfers), 1)

    def test_reusing_key_for_another_payload_is_rejected(self):
        self.store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 250, "idempotency_key": "k1"})
        with self.assertRaises(ValueError):
            self.store.create_transfer({"sender_id": "alice", "recipient_id": "bob", "amount_cents": 900, "idempotency_key": "k1"})

    def test_concurrent_retries_move_money_once(self):
        payload = {"sender_id": "alice", "recipient_id": "bob", "amount_cents": 250, "idempotency_key": "k1"}
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.store.create_transfer(payload), range(32)))
        self.assertEqual(len(self.store.transfers), 1)
        self.assertEqual(self.store.wallets["alice"]["balance_cents"], 750)
        self.assertTrue(all(result == results[0] for result in results))


if __name__ == "__main__":
    unittest.main()
