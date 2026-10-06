from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from factoryproof.runner import FactoryRunner


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    runner = FactoryRunner(root, delay=0)
    run = runner.start_run()
    run_id = run["id"]
    deadline = time.time() + 30
    while time.time() < deadline:
        current = runner.get_run(run_id)
        if current and current["status"] in {"awaiting_human", "shipped", "failed"}:
            break
        time.sleep(0.05)
    else:
        raise SystemExit("factory run timed out")
    if not current or current["status"] != "awaiting_human":
        print(json.dumps(current, indent=2))
        raise SystemExit(1)
    current = runner.approve(run_id)
    print(json.dumps(current, indent=2))


if __name__ == "__main__":
    main()
