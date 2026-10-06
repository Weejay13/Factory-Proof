from dataclasses import dataclass


@dataclass(frozen=True)
class Wallet:
    user_id: str
    balance_cents: int


@dataclass(frozen=True)
class Transfer:
    transfer_id: str
    idempotency_key: str
    sender_id: str
    recipient_id: str
    amount_cents: int


class WalletService:
    def __init__(self) -> None:
        self._wallets = {}
        self._transfers = []
        self._by_key = {}

    def create_wallet(self, user_id, initial_cents=0):
        if not user_id or initial_cents < 0:
            raise ValueError("invalid wallet")
        wallet = Wallet(user_id, initial_cents)
        self._wallets[user_id] = wallet
        return wallet

    def transfer(self, sender_id, recipient_id, amount_cents, idempotency_key):
        if amount_cents <= 0 or not idempotency_key:
            raise ValueError("invalid transfer")
        if idempotency_key in self._by_key:
            return self._by_key[idempotency_key]
        sender = self._wallets[sender_id]
        recipient = self._wallets[recipient_id]
        if sender.balance_cents < amount_cents:
            raise ValueError("insufficient funds")
        sender = Wallet(sender.user_id, sender.balance_cents - amount_cents)
        recipient = Wallet(recipient.user_id, recipient.balance_cents + amount_cents)
        self._wallets[sender_id] = sender
        self._wallets[recipient_id] = recipient
        transfer = Transfer(idempotency_key, idempotency_key, sender_id, recipient_id, amount_cents)
        self._transfers.append(transfer)
        self._by_key[idempotency_key] = transfer
        return transfer
