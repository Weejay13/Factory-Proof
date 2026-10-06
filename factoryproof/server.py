from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .runner import DEFAULT_TASK, FactoryRunner


class FactoryRequestHandler(BaseHTTPRequestHandler):
    runner: FactoryRunner
    web_root: Path
    root: Path

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json({"status": "ok", "service": "factoryproof"})
            return
        if path == "/api/run":
            self._json(self.runner.latest() or {"status": "idle", "run": None})
            return
        if path == "/api/report":
            run = self.runner.latest()
            if run is None:
                self._json({"error": "no run has been created"}, HTTPStatus.NOT_FOUND)
            else:
                self._json({"run_id": run["id"], "status": run["status"], "report": run.get("report", {}), "artifacts": run.get("artifacts", {})})
            return
        if path.startswith("/api/runs/"):
            run_id = path.rsplit("/", 1)[-1]
            run = self.runner.get_run(run_id)
            if run is None:
                self._json({"error": "run not found"}, HTTPStatus.NOT_FOUND)
            else:
                self._json(run)
            return
        self._static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path in {"/api/run", "/api/approve"} and self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
            self._json({"error": "Content-Type must be application/json"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return
        if path == "/api/run":
            try:
                payload = self._body()
            except ValueError as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            mode = str(payload.get("mode") or "offline")
            if mode != "offline":
                self._json({"error": "The local server only runs the offline rehearsal; use the BAND Desktop room for live execution."}, HTTPStatus.CONFLICT)
                return
            run = self.runner.start_run(
                task=str(payload.get("task") or DEFAULT_TASK),
                mode=mode,
            )
            self._json(run, HTTPStatus.ACCEPTED)
            return
        if path == "/api/approve":
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host", ""):
                self._json({"error": "approval origin is not allowed"}, HTTPStatus.FORBIDDEN)
                return
            try:
                payload = self._body()
            except ValueError as error:
                self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
                return
            run_id = str(payload.get("run_id") or "")
            if not run_id:
                self._json({"error": "run_id is required for approval"}, HTTPStatus.BAD_REQUEST)
                return
            run = self.runner.approve(run_id)
            if run is None:
                self._json({"error": "run not found"}, HTTPStatus.NOT_FOUND)
            else:
                self._json(run)
            return
        self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _body(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        if length > 64_000:
            raise ValueError("request body is too large")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def _static(self, path: str) -> None:
        if path == "/README.md":
            candidate = (self.root / "README.md").resolve()
        else:
            relative = "index.html" if path == "/" else path.lstrip("/")
            candidate = (self.web_root / relative).resolve()
        if self.web_root.resolve() not in candidate.parents and candidate != self.web_root.resolve() and candidate != (self.root / "README.md").resolve():
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'")
        self.end_headers()
        self.wfile.write(body)


def create_server(root: Path, host: str = "127.0.0.1", port: int = 8787, delay: float = 0.0) -> ThreadingHTTPServer:
    web_root = root / "web"
    runner = FactoryRunner(root, delay=delay)
    handler = type("BoundFactoryRequestHandler", (FactoryRequestHandler,), {"runner": runner, "web_root": web_root, "root": root})
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FactoryProof local factory")
    parser.add_argument("--host", default=os.getenv("FACTORYPROOF_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FACTORYPROOF_PORT", "8787")))
    parser.add_argument("--delay", type=float, default=float(os.getenv("FACTORYPROOF_DELAY", "0")))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    server = create_server(root, args.host, args.port, args.delay)
    print(f"FactoryProof listening at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
