# Live BAND room

FactoryProof's local dashboard works without credentials. A real submission should also show the same four roles coordinating in a BAND room.

## Prerequisites

- Python 3.11+
- A BAND account
- A separate BAND Remote Agent identity for each role
- `band-sdk` with the Anthropic extra for coordinator and critic
- Claude Code installed and signed in for builder and verifier, or those roles run from Band Desktop

Install the optional dependency in an isolated environment:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[band]"
```

For the filesystem-enabled builder, install the heavier adapter separately when needed:

```bash
python -m pip install -e ".[band-claude]"
```

Copy `band_config.example.yaml` to `band_config.yaml`, add the four BAND agent IDs and keys, and keep that file private. The config file and `.env` are ignored by Git.

Check the local prerequisites without printing secrets:

```bash
python3.11 -m band_agents.preflight
```

## Run the room

Use four terminals from this project directory:

```bash
python -m band_agents.agent coordinator
python -m band_agents.agent verifier
python -m band_agents.agent critic
python -m band_agents.agent builder
```

The coordinator and critic use the lighter Anthropic adapter by default. The builder and verifier use the Claude SDK adapter by default so they can run local checks in a dedicated workspace with manual approvals. In Band, create one room and add the four registered agents. The coordinator is the architect: it creates the room, recruits the builder and verifier, and asks the critic to review the final evidence packet. Turn on execution events in Band Desktop or the SDK logs so tool calls and findings appear in the room.

Start the room with the track-specific task in `band_agents/pocketful_task.md`, or paste:

```text
@Coordinator Build the case: a Pocketful-style wallet transfer service must preserve money under retries and concurrent requests, reject malformed or insufficient transfers, and keep a reviewable audit trail. Recruit the builder and verifier, keep the release critic load-bearing, and stop at the human promotion gate.
```

The project agents are deliberately separate identities. The coordinator's finding changes the builder's work, the verifier's veto changes the next revision, and the critic can block the promotion. That dependent handoff is the product; a transcript of independent status updates is not enough.
