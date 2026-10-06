import unittest

from wallet_service import WalletService


class PublicWalletTests(unittest.TestCase):
    def test_transfer_once(self):
        service = WalletService()
        service.create_wallet("alice", 1000)
        service.create_wallet("bob", 0)
        self.assertEqual(service.transfer("alice", "bob", 250, "k1").amount_cents, 250)


if __name__ == "__main__":
    unittest.main()
