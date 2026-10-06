from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check FactoryProof BAND prerequisites without printing secrets")
    parser.add_argument("--config", type=Path, default=Path("band_config.yaml"))
    args = parser.parse_args()
    roles = ("coordinator", "builder", "verifier", "critic")
    checks = {
        "python_311_or_newer": __import__("sys").version_info >= (3, 11),
        "band_sdk_installed": importlib.util.find_spec("band") is not None,
        "config_present": args.config.exists(),
        "role_credentials": {role: bool(os.getenv(f"FACTORYPROOF_{role.upper()}_AGENT_ID") and (os.getenv(f"FACTORYPROOF_{role.upper()}_BAND_API_KEY") or os.getenv("BAND_API_KEY"))) for role in roles},
        "anthropic_key_present": bool(os.getenv("ANTHROPIC_API_KEY")),
    }
    print(checks)
    return 0 if checks["python_311_or_newer"] and checks["band_sdk_installed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
