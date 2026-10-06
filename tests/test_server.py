import json
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import Request, urlopen

from factoryproof.server import create_server


class ServerTests(unittest.TestCase):
    def test_api_can_start_and_approve_a_run(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "web").mkdir()
            (root / "web" / "index.html").write_text("FactoryProof", encoding="utf-8")
            server = create_server(root, "127.0.0.1", 0, delay=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_address[1]}"
                with urlopen(base + "/api/health") as response:
                    self.assertEqual(json.loads(response.read())["status"], "ok")
                run = self._post(base + "/api/run", {"mode": "offline"})
                self.assertIn(run["status"], {"queued", "planning", "implementing", "revising", "reviewing", "awaiting_human", "shipped"})
                deadline = time.time() + 10
                while run["status"] != "awaiting_human" and time.time() < deadline:
                    time.sleep(0.01)
                    with urlopen(base + "/api/run") as response:
                        run = json.loads(response.read())
                self.assertEqual(run["status"], "awaiting_human")
                approved = self._post(base + "/api/approve", {"run_id": run["id"]})
                self.assertEqual(approved["status"], "shipped")
                self.assertEqual(approved["human_gate"], "approved")
                with urlopen(base + "/api/report") as response:
                    report = json.loads(response.read())
                self.assertEqual(report["run_id"], run["id"])
                self.assertIn("artifacts", report)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    @staticmethod
    def _post(url, payload):
        request = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request) as response:
            return json.loads(response.read())


if __name__ == "__main__":
    unittest.main()
