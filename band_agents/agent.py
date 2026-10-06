from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from .prompts import load_prompt


if load_dotenv is not None:
    load_dotenv()


def credentials(role: str, config_path: Path) -> tuple[str, str]:
    prefix = f"FACTORYPROOF_{role.upper()}"
    agent_id = os.getenv(f"{prefix}_AGENT_ID")
    api_key = os.getenv(f"{prefix}_BAND_API_KEY") or os.getenv("BAND_API_KEY")
    if agent_id and api_key:
        return agent_id, api_key
    from band.config import load_agent_config

    return load_agent_config(role, config_path=config_path)


def build_adapter(role: str, prompt: str, cwd: Path, adapter_kind: str):
    from band import Emit

    model = os.getenv("FACTORYPROOF_BAND_MODEL", "claude-sonnet-4-5")
    if adapter_kind == "claude":
        from band.adapters import ClaudeSDKAdapter

        settings = {
            "model": model,
            "custom_section": prompt,
            "cwd": str(cwd),
            "emit": {Emit.TOOL_CALLS, Emit.USAGE},
            "approval_mode": "manual",
            "approval_wait_timeout_s": 300,
        }
        settings["permission_mode"] = "acceptEdits" if role == "builder" else "plan"
        return ClaudeSDKAdapter(**settings)
    from band.adapters import AnthropicAdapter

    if role in {"builder", "verifier"}:
        raise RuntimeError(f"{role} requires the Claude adapter or Band Desktop tools")
    return AnthropicAdapter(model=model, prompt=prompt, emit={Emit.TOOL_CALLS})


async def run_agent(role: str, config_path: Path, cwd: Path, adapter_kind: str) -> None:
    from band import Agent

    agent_id, api_key = credentials(role, config_path)
    adapter = build_adapter(role, load_prompt(role), cwd, adapter_kind)
    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
        ws_url=os.getenv("BAND_WS_URL", "wss://app.band.ai/api/v1/socket/websocket"),
        rest_url=os.getenv("BAND_REST_URL", "https://app.band.ai"),
    )
    logging.info("FactoryProof %s connected to BAND", role)
    await agent.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one FactoryProof role in BAND")
    parser.add_argument("role", choices=["coordinator", "builder", "verifier", "critic"])
    parser.add_argument("--config", type=Path, default=Path("band_config.yaml"))
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--adapter", choices=["anthropic", "claude"], default=None)
    args = parser.parse_args()
    adapter_kind = args.adapter or os.getenv("FACTORYPROOF_BAND_ADAPTER") or ("claude" if args.role in {"builder", "verifier"} else "anthropic")
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_agent(args.role, args.config, args.cwd.resolve(), adapter_kind))


if __name__ == "__main__":
    main()
