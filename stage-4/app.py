from __future__ import annotations

import argparse
import hashlib
import json
import threading
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class Store:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.wallets: dict[str, dict] = {}
        self.transfers: dict[str, dict] = {}
        self.by_key: dict[str, dict] = {}
        self.refunds: dict[str, dict] = {}
        self.audit: list[dict] = []

    def create_wallet(self, payload: dict) -> dict:
        user_id = str(payload.get("user_id", "")).strip()
        balance = payload.get("balance_cents", 0)
        if not user_id or not isinstance(balance, int) or balance < 0:
            raise ValueError("user_id and non-negative balance_cents are required")
        with self.lock:
            if user_id in self.wallets:
                raise ValueError("wallet already exists")
            wallet = {"user_id": user_id, "balance_cents": balance}
            self.wallets[user_id] = wallet
            self.audit.append({"event": "wallet_created", "user_id": user_id})
            return wallet

    def create_transfer(self, payload: dict) -> dict:
        sender_id = str(payload.get("sender_id", "")).strip()
        recipient_id = str(payload.get("recipient_id", "")).strip()
        amount = payload.get("amount_cents")
        key = str(payload.get("idempotency_key", "")).strip()
        if not sender_id or not recipient_id or not isinstance(amount, int) or amount <= 0 or not key:
            raise ValueError("sender_id, recipient_id, positive amount_cents, and idempotency_key are required")
        fingerprint = hashlib.sha256(f"{sender_id}:{recipient_id}:{amount}".encode()).hexdigest()
        with self.lock:
            existing = self.by_key.get(key)
            if existing is not None:
                if existing["request_fingerprint"] != fingerprint:
                    raise ValueError("idempotency key was already used for another transfer")
                return self._public_transfer(existing)
            if sender_id not in self.wallets or recipient_id not in self.wallets:
                raise LookupError("wallet not found")
            sender = self.wallets[sender_id]
            recipient = self.wallets[recipient_id]
            if sender["balance_cents"] < amount:
                raise ValueError("insufficient funds")
            sender["balance_cents"] -= amount
            recipient["balance_cents"] += amount
            transfer = {"transfer_id": uuid.uuid4().hex, "idempotency_key": key, "sender_id": sender_id, "recipient_id": recipient_id, "amount_cents": amount, "status": "completed", "request_fingerprint": fingerprint}
            self.transfers[transfer["transfer_id"]] = transfer
            self.by_key[key] = transfer
            self.audit.append({"event": "transfer_completed", "transfer_id": transfer["transfer_id"], "idempotency_key": key})
            return self._public_transfer(transfer)

    def refund(self, transfer_id: str, payload: dict) -> dict:
        key = str(payload.get("idempotency_key", "")).strip()
        if not key:
            raise ValueError("idempotency_key is required")
        with self.lock:
            existing = self.refunds.get(key)
            if existing is not None:
                return existing
            transfer = self.transfers.get(transfer_id)
            if transfer is None:
                raise LookupError("transfer not found")
            if transfer["status"] == "refunded":
                raise ValueError("transfer already refunded")
            sender = self.wallets[transfer["sender_id"]]
            recipient = self.wallets[transfer["recipient_id"]]
            amount = transfer["amount_cents"]
            sender["balance_cents"] += amount
            recipient["balance_cents"] -= amount
            transfer["status"] = "refunded"
            refund = {"refund_id": uuid.uuid4().hex, "transfer_id": transfer_id, "idempotency_key": key, "amount_cents": amount, "status": "completed"}
            self.refunds[key] = refund
            self.audit.append({"event": "transfer_refunded", "transfer_id": transfer_id, "idempotency_key": key})
            return refund

    @staticmethod
    def _public_transfer(transfer: dict) -> dict:
        return {key: value for key, value in transfer.items() if key != "request_fingerprint"}


class Handler(BaseHTTPRequestHandler):
    store: Store

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/api", "/api/health", "/health"}:
            return self._json({"service": "pocketful-stage-4", "status": "ok", "extension": "refunds"})
        if path in {"/api/transfers", "/transfers"}:
            return self._json({"transfers": [self.store._public_transfer(item) for item in self.store.transfers.values()]})
        if path in {"/api/audit", "/audit"}:
            return self._json({"audit": self.store.audit})
        if path.startswith("/api/wallets/") or path.startswith("/wallets/"):
            wallet = self.store.wallets.get(path.rsplit("/", 1)[-1])
            if wallet is None:
                return self._json({"error": "wallet not found"}, HTTPStatus.NOT_FOUND)
            return self._json(wallet)
        return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._body()
            if path in {"/api/wallets", "/wallets"}:
                return self._json(self.store.create_wallet(payload), HTTPStatus.CREATED)
            if path in {"/api/transfers", "/transfers"}:
                return self._json(self.store.create_transfer(payload), HTTPStatus.CREATED)
            parts = path.strip("/").split("/")
            if len(parts) == 4 and parts[-1] == "refund" and parts[-3] == "transfers":
                return self._json(self.store.refund(parts[-2], payload), HTTPStatus.CREATED)
            return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except ValueError as error:
            return self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except LookupError as error:
            return self._json({"error": str(error)}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 64_000:
            raise ValueError("request body is required and must be small")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), type("BoundHandler", (Handler,), {"store": Store()}))
    print(f"Pocketful stage 4 listening on {args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
