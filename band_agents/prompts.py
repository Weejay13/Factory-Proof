from pathlib import Path


PROMPTS = {
    "coordinator": "coordinator.md",
    "builder": "builder.md",
    "verifier": "verifier.md",
    "critic": "critic.md",
}


def load_prompt(role: str) -> str:
    return (Path(__file__).parent / "prompts" / PROMPTS[role]).read_text(encoding="utf-8")
