from __future__ import annotations

import argparse
import json
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


INDEX = '''<!doctype html><html><head><meta name="viewport" content="width=device-width"><title>Pocketful Wallet</title><style>body{font:16px system-ui;max-width:760px;margin:40px auto;padding:0 20px}input,button{padding:10px;margin:4px}section{border:1px solid #ddd;padding:18px;margin:18px 0}#transfer-status{min-height:24px}</style></head><body><h1>Pocketful Wallet</h1><section><h2>Create wallet</h2><input data-testid="wallet-user-id" id="wallet-user-id" placeholder="user id"><input data-testid="wallet-balance" id="wallet-balance" type="number" value="0"><button data-testid="create-wallet" onclick="createWallet()">Create</button><p id="wallet-status"></p></section><section><h2>Transfer</h2><input data-testid="sender-id" placeholder="sender"><input data-testid="recipient-id" placeholder="recipient"><input data-testid="amount-cents" type="number" value="0"><input data-testid="idempotency-key" placeholder="idempotency key"><button data-testid="create-transfer" onclick="createTransfer()">Send</button><p id="transfer-status" data-testid="transfer-status"></p></section><section><h2>Audit trail</h2><pre id="audit-list" data-testid="audit-list"></pre></section><script>async function post(path,body){return (await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json()}async function load(){document.getElementById('audit-list').textContent=JSON.stringify(await (await fetch('/api/transfers')).json(),null,2)}async function createWallet(){const r=await post('/api/wallets',{user_id:document.getElementById('wallet-user-id').value,balance_cents:Number(document.getElementById('wallet-balance').value)});document.getElementById('wallet-status').textContent=JSON.stringify(r)}async function createTransfer(){const r=await post('/api/transfers',{sender_id:document.getElementById('sender-id').value,recipient_id:document.getElementById('recipient-id').value,amount_cents:Number(document.getElementById('amount-cents').value),idempotency_key:document.getElementById('idempotency-key').value});document.getElementById('transfer-status').textContent=JSON.stringify(r);load()}load()</script></body></html>'''


class Store:
    def __init__(self) -> None:
        self.wallets: dict[str, dict] = {}
        self.transfers: dict[str, dict] = {}

    def create_wallet(self, payload: dict) -> dict:
        user_id = str(payload.get("user_id", "")).strip()
        balance = payload.get("balance_cents", 0)
        if not user_id or not isinstance(balance, int) or balance < 0:
            raise ValueError("user_id and non-negative balance_cents are required")
        wallet = {"user_id": user_id, "balance_cents": balance}
        self.wallets[user_id] = wallet
        return wallet

    def create_transfer(self, payload: dict) -> dict:
        sender_id = str(payload.get("sender_id", "")).strip()
        recipient_id = str(payload.get("recipient_id", "")).strip()
        amount = payload.get("amount_cents")
        key = str(payload.get("idempotency_key", "")).strip()
        if not sender_id or not recipient_id or not isinstance(amount, int) or amount <= 0 or not key:
            raise ValueError("sender_id, recipient_id, positive amount_cents, and idempotency_key are required")
        if sender_id not in self.wallets or recipient_id not in self.wallets:
            raise LookupError("wallet not found")
        sender = self.wallets[sender_id]
        recipient = self.wallets[recipient_id]
        if sender["balance_cents"] < amount:
            raise ValueError("insufficient funds")
        sender["balance_cents"] -= amount
        recipient["balance_cents"] += amount
        transfer = {"transfer_id": uuid.uuid4().hex, "idempotency_key": key, "sender_id": sender_id, "recipient_id": recipient_id, "amount_cents": amount, "status": "completed"}
        self.transfers[transfer["transfer_id"]] = transfer
        return transfer


class Handler(BaseHTTPRequestHandler):
    store: Store

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            body = INDEX.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path in {"/api", "/api/health", "/health"}:
            return self._json({"service": "pocketful-stage-2", "status": "ok"})
        if path in {"/api/transfers", "/transfers"}:
            return self._json({"transfers": list(self.store.transfers.values())})
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
    print(f"Pocketful stage 2 listening on {args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
