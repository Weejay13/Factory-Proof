import unittest

from wallet_service import WalletService


class SealedAcceptanceTests(unittest.TestCase):
    def test_retry_does_not_double_spend(self):
        service = WalletService()
        service.create_wallet("alice", 1000)
        service.create_wallet("bob", 0)
        first = service.transfer("alice", "bob", 250, "k1")
        retry = service.transfer("alice", "bob", 250, "k1")
        self.assertEqual(first, retry)
        self.assertEqual(len(service._transfers), 1)


if __name__ == "__main__":
    unittest.main()
