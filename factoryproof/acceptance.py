from __future__ import annotations

import difflib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


BASELINE_SOURCE = '''from dataclasses import dataclass\n\n\n@dataclass(frozen=True)\nclass Wallet:\n    user_id: str\n    balance_cents: int\n\n\n@dataclass(frozen=True)\nclass Transfer:\n    transfer_id: str\n    idempotency_key: str\n    sender_id: str\n    recipient_id: str\n    amount_cents: int\n\n\nclass WalletService:\n    def __init__(self) -> None:\n        self._wallets: dict[str, Wallet] = {}\n        self._transfers: list[Transfer] = []\n\n    def create_wallet(self, user_id: str, initial_cents: int = 0) -> Wallet:\n        if not user_id:\n            raise ValueError("user_id is required")\n        wallet = Wallet(user_id, initial_cents)\n        self._wallets[user_id] = wallet\n        return wallet\n\n    def transfer(self, sender_id: str, recipient_id: str, amount_cents: int, idempotency_key: str) -> Transfer:\n        if not sender_id or not recipient_id:\n            raise ValueError("sender_id and recipient_id are required")\n        sender = self._wallets[sender_id]\n        recipient = self._wallets[recipient_id]\n        sender = Wallet(sender.user_id, sender.balance_cents - amount_cents)\n        recipient = Wallet(recipient.user_id, recipient.balance_cents + amount_cents)\n        self._wallets[sender_id] = sender\n        self._wallets[recipient_id] = recipient\n        transfer = Transfer(idempotency_key, idempotency_key, sender_id, recipient_id, amount_cents)\n        self._transfers.append(transfer)\n        return transfer\n'''

CANDIDATE_V1_SOURCE = '''from dataclasses import dataclass\n\n\n@dataclass(frozen=True)\nclass Wallet:\n    user_id: str\n    balance_cents: int\n\n\n@dataclass(frozen=True)\nclass Transfer:\n    transfer_id: str\n    idempotency_key: str\n    sender_id: str\n    recipient_id: str\n    amount_cents: int\n\n\nclass WalletService:\n    def __init__(self) -> None:\n        self._wallets: dict[str, Wallet] = {}\n        self._transfers: list[Transfer] = []\n\n    def create_wallet(self, user_id: str, initial_cents: int = 0) -> Wallet:\n        if not user_id or initial_cents < 0:\n            raise ValueError("user_id and a non-negative balance are required")\n        wallet = Wallet(user_id, initial_cents)\n        self._wallets[user_id] = wallet\n        return wallet\n\n    def transfer(self, sender_id: str, recipient_id: str, amount_cents: int, idempotency_key: str) -> Transfer:\n        if not sender_id or not recipient_id or amount_cents <= 0 or not idempotency_key:\n            raise ValueError("valid wallets, amount, and idempotency_key are required")\n        sender = self._wallets[sender_id]\n        recipient = self._wallets[recipient_id]\n        if sender.balance_cents < amount_cents:\n            raise ValueError("insufficient funds")\n        sender = Wallet(sender.user_id, sender.balance_cents - amount_cents)\n        recipient = Wallet(recipient.user_id, recipient.balance_cents + amount_cents)\n        self._wallets[sender_id] = sender\n        self._wallets[recipient_id] = recipient\n        transfer = Transfer(idempotency_key, idempotency_key, sender_id, recipient_id, amount_cents)\n        self._transfers.append(transfer)\n        return transfer\n'''

CANDIDATE_V2_SOURCE = '''from dataclasses import dataclass\n\n\n@dataclass(frozen=True)\nclass Wallet:\n    user_id: str\n    balance_cents: int\n\n\n@dataclass(frozen=True)\nclass Transfer:\n    transfer_id: str\n    idempotency_key: str\n    sender_id: str\n    recipient_id: str\n    amount_cents: int\n\n\nclass WalletService:\n    def __init__(self) -> None:\n        self._wallets: dict[str, Wallet] = {}\n        self._transfers: list[Transfer] = []\n        self._by_key: dict[str, Transfer] = {}\n\n    def create_wallet(self, user_id: str, initial_cents: int = 0) -> Wallet:\n        if not user_id or initial_cents < 0:\n            raise ValueError("user_id and a non-negative balance are required")\n        wallet = Wallet(user_id, initial_cents)\n        self._wallets[user_id] = wallet\n        return wallet\n\n    def transfer(self, sender_id: str, recipient_id: str, amount_cents: int, idempotency_key: str) -> Transfer:\n        if not sender_id or not recipient_id or amount_cents <= 0 or not idempotency_key:\n            raise ValueError("valid wallets, amount, and idempotency_key are required")\n        if idempotency_key in self._by_key:\n            return self._by_key[idempotency_key]\n        sender = self._wallets[sender_id]\n        recipient = self._wallets[recipient_id]\n        if sender.balance_cents < amount_cents:\n            raise ValueError("insufficient funds")\n        sender = Wallet(sender.user_id, sender.balance_cents - amount_cents)\n        recipient = Wallet(recipient.user_id, recipient.balance_cents + amount_cents)\n        self._wallets[sender_id] = sender\n        self._wallets[recipient_id] = recipient\n        transfer = Transfer(idempotency_key, idempotency_key, sender_id, recipient_id, amount_cents)\n        self._transfers.append(transfer)\n        self._by_key[idempotency_key] = transfer\n        return transfer\n'''

PUBLIC_TEST_SOURCE = '''import unittest\n\nfrom wallet_service import WalletService\n\n\nclass PublicWalletTests(unittest.TestCase):\n    def test_creates_wallets_and_transfers_once(self):\n        service = WalletService()\n        service.create_wallet("alice", 1000)\n        service.create_wallet("bob", 0)\n        transfer = service.transfer("alice", "bob", 250, "pay-1")\n        self.assertEqual(transfer.amount_cents, 250)\n        self.assertEqual(service._wallets["alice"].balance_cents, 750)\n        self.assertEqual(service._wallets["bob"].balance_cents, 250)\n\n    def test_rejects_invalid_amount_and_insufficient_funds(self):\n        service = WalletService()\n        service.create_wallet("alice", 10)\n        service.create_wallet("bob", 0)\n        with self.assertRaises(ValueError):\n            service.transfer("alice", "bob", 0, "pay-1")\n        with self.assertRaises(ValueError):\n            service.transfer("alice", "bob", 11, "pay-2")\n'''

HIDDEN_TEST_SOURCE = '''import unittest\n\nfrom wallet_service import WalletService\n\n\nclass SealedAcceptanceTests(unittest.TestCase):\n    def test_retry_returns_original_transfer_without_double_spend(self):\n        service = WalletService()\n        service.create_wallet("alice", 1000)\n        service.create_wallet("bob", 0)\n        original = service.transfer("alice", "bob", 250, "pay-1")\n        retry = service.transfer("alice", "bob", 250, "pay-1")\n        self.assertEqual(retry, original)\n        self.assertEqual(service._wallets["alice"].balance_cents, 750)\n        self.assertEqual(service._wallets["bob"].balance_cents, 250)\n        self.assertEqual(len(service._transfers), 1)\n\n    def test_retry_with_different_payload_does_not_move_more_money(self):\n        service = WalletService()\n        service.create_wallet("alice", 1000)\n        service.create_wallet("bob", 0)\n        service.transfer("alice", "bob", 250, "pay-1")\n        retry = service.transfer("alice", "bob", 900, "pay-1")\n        self.assertEqual(retry.amount_cents, 250)\n        self.assertEqual(service._wallets["alice"].balance_cents, 750)\n'''


def make_patch(before: str, after: str, filename: str = "wallet_service.py") -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )


def _run_python_test(source: str, test_source: str) -> dict[str, Any]:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="factoryproof-") as directory:
        root = Path(directory)
        (root / "wallet_service.py").write_text(source, encoding="utf-8")
        (root / "test_wallet_service.py").write_text(test_source, encoding="utf-8")
        environment = {
            "PATH": os.getenv("PATH", ""),
            "PYTHONPATH": str(root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": str(root),
        }
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "-q"],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
        )
    output = (result.stdout + result.stderr).strip()
    return {
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "output": output[-4000:],
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
    }


def verify_candidate(source: str) -> dict[str, Any]:
    return {
        "public": _run_python_test(source, PUBLIC_TEST_SOURCE),
        "sealed": _run_python_test(source, HIDDEN_TEST_SOURCE),
    }


def demo_sources() -> dict[str, str]:
    return {
        "baseline": BASELINE_SOURCE,
        "v1": CANDIDATE_V1_SOURCE,
        "v2": CANDIDATE_V2_SOURCE,
    }
