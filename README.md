# FactoryProof

**The software factory that proves its work.**

FactoryProof is a BAND-native software factory for the WeAreDevelopers x BAND Dark Factory hackathon. A coordinator scopes a case and recruits specialists, a builder produces a bounded change, a verifier runs independent checks, a critic can veto unsupported evidence, and a human owner controls promotion.

The selected reference track is **Pocketful**: a wallet-and-transfer service where money must not be created, destroyed, or spent twice under retries, concurrent requests, and exact integer-cent accounting. The factory is track-agnostic; the Pocketful contract belongs in the room task, not in the seat mandates.

## Collaboration proof

The room is load-bearing:

- the coordinator's plan changes the builder's work
- the verifier's veto changes the next revision
- the critic's recommendation controls the human gate
- execution events and evidence are preserved for review

The local dashboard is explicitly an **offline rehearsal mode**, not a claim that a BAND room ran. A real submission must record the BAND Desktop room that generated the result. The optional runners in `band_agents/` show the live BAND integration path.

## Stage layout

The repository contains a complete reference service for each released stage shape:

- `stage-1/` — JSON API
- `stage-2/` — JSON API plus browser UI with explicit `data-testid` attributes
- `stage-3/` — atomic transfer path, idempotency replay protection, and audit stream
- `stage-4/` — same domain extended with idempotent refunds

Each stage is self-contained and has its own Dockerfile and tests. The official kickoff specification and harness remain authoritative for exact endpoint names, response shapes, selectors, resource limits, and stage grading; adapt the reference services when those files are released.

## Run the local factory

Requires Python 3.10 or newer.

```bash
cd /home/wesley/Desktop/FactoryProof
python3 -m factoryproof.server
```

Open `http://127.0.0.1:8787`, then click **Run the wallet transfer case**. The offline rehearsal mirrors the BAND handoffs but does not submit or promote a real service.

Run the deterministic rehearsal directly:

```bash
python3 scripts/demo.py
```

Run all local checks:

```bash
python3 scripts/verify.py
```

## Run a stage service

```bash
cd stage-3
python3 app.py --host 127.0.0.1 --port 8080
```

The same command works in `stage-1`, `stage-2`, or `stage-4`. A stage container is built from that stage's Dockerfile and makes no outbound network calls.

## Repository map

- `factoryproof/` — offline evidence runner and local dashboard API
- `web/` — dashboard UI
- `stage-1/` through `stage-4/` — complete stage services
- `mandates/` — generic seat mandates
- `factory_description.md` — factory definition
- `band_agents/` — optional BAND role runners, prompts, and task
- `BAND_ROOM_EXPORT_RUNBOOK.md` — step-by-step room, recording, and export instructions
- `evidence/` — submission evidence checklist and templates
- `tests/` — local dashboard/API tests

## Live BAND setup

Start with [`BAND_ROOM_EXPORT_RUNBOOK.md`](BAND_ROOM_EXPORT_RUNBOOK.md) for the official Desktop room, recording, and export procedure. Then follow `band_agents/README.md` for the optional SDK runner path. Live mode requires Python 3.11+, a BAND account, and four separately registered Remote Agents. The seat mandates in `mandates/` are generic by design; the track-specific task is `band_agents/pocketful_task.md`.

Never commit `band_config.yaml`, `.env`, API keys, or real secrets.

## Submission checklist

Before submitting:

- run `./harness check --strict` and the official `harness check` after kickoff
- record the BAND Desktop room that generated the service
- export the room with the official harness command
- record a video containing both the room and a walkthrough
- publish one public GitHub repository
- provide a clean-container application URL
- attach a cover image and slide presentation
- select the Pocketful track in the Lablab form

The local `harness` wrapper is only a preflight until the official harness is released.

## Demo story

1. Start the local dashboard and select the wallet transfer case.
2. Show the coordinator recruiting the builder and verifier.
3. Show the first candidate passing public checks but failing the sealed retry check.
4. Show the verifier's `BLOCKED` event and the builder's revision.
5. Show the critic's recommendation and the human gate.
6. In the recorded BAND room, show the actual agents performing the same handoffs.
7. Approve only after the service passes the official stage harness.

**Pitch:** the factory does not trust an agent's confidence; it ships only evidence that survives independent checks and a human decision.

## Event links

- [WeAreDevelopers x BAND: Dark Factory](https://lablab.ai/ai-hackathons/wearedevelopers-hackathon)
- [BAND Hacker Guide](https://www.band.ai/hacker-guide)
- [BAND documentation](https://docs.band.ai/)
