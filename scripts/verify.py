from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run(command: list[str], root: Path) -> None:
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout.strip())


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    run([sys.executable, "-m", "compileall", "-q", "factoryproof", "band_agents", "tests", "scripts", "stage-1", "stage-2", "stage-3", "stage-4"], root)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root)
    for stage in ("stage-1", "stage-2", "stage-3", "stage-4"):
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], root / stage)
    node = subprocess.run(["node", "--check", "web/app.js"], cwd=root, text=True, capture_output=True)
    if node.returncode:
        print(node.stderr, file=sys.stderr)
        raise SystemExit(node.returncode)
    print(json.dumps({"python": "ok", "javascript": "ok"}))


if __name__ == "__main__":
    main()
