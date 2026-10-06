# BAND room and evidence export runbook

This runbook covers the required submission evidence for **WeAreDevelopers x BAND: Dark Factory**. It is for the BAND Desktop room, not the IBM Bob event and not a room that merely built this repository.

## 1. Install and prepare BAND Desktop

BAND Desktop is the current name for Jam. Use macOS or Linux.

1. Download Band Desktop from the official [BAND Desktop documentation](https://docs.band.ai/jam).
2. Sign in with your BAND account.
3. Let Band Desktop install or repair the `band` CLI and `band-peer` plugin.
4. Install and sign in to Claude Code if you will use Claude Code sessions.
5. Restart Claude Code after installing or repairing the plugin.
6. Click **Recheck** until every readiness check is green.

The local SDK path is optional. It requires Python 3.11+, a BAND Remote Agent identity, and credentials. The Desktop path is the recommended way to produce the recorded room.

## 2. Register four distinct agents

In the BAND agent dashboard, create four separate Remote Agents with descriptive names:

| Seat | Responsibility |
| --- | --- |
| Case Coordinator | Scope, recruit, route, and escalate |
| Patch Builder | Implement only the approved contract |
| Quality Verifier | Run independent checks and preserve failures |
| Release Critic | Challenge evidence and block unsupported promotion |

Use a different UUID and API key for every agent. Never reuse one identity: BAND allows one live connection per agent identity, and a duplicate connection displaces the older one. Keep credentials in the ignored `band_config.yaml` or environment variables; never commit them.

## 3. Create the submission room

The build crew room is not the submission room. The submission room must contain the project agents working the Pocketful case.

1. Open BAND Desktop and start the Coordinator session.
2. Run `/jam` and identify the session as the architect/Coordinator.
3. Create one room named for FactoryProof or the Pocketful case.
4. Start three more Claude Code sessions and have them join the same room.
5. Confirm that all four agents appear as connected participants.
6. Turn on tool, execution, and event visibility before recording.

Use the generic seat mandates in `mandates/`. Do not add the track contract to those mandate files.

## 4. Run the case

Send the track-specific task from `band_agents/pocketful_task.md` to the Coordinator. The task is deliberately separate from the mandates.

The room should visibly perform this flow:

```text
Coordinator scopes the case
  -> mentions Builder with the bounded contract
  -> Builder implements and mentions Verifier with evidence
  -> Verifier posts failed or passing checks
  -> Builder revises when the verifier blocks
  -> Verifier hands the evidence to Critic
  -> Critic posts BLOCKED or a recommendation
  -> Critic mentions the human owner
  -> Human owner promotes or rejects the result
```

A room that only posts independent status messages is not sufficient. The next action must depend on the previous finding. Preserve failures; do not hide them to make the demo look clean.

## 5. Record the room

Use a screen recorder that captures the BAND Desktop room and the service walkthrough. Keep the room visible while the agents work.

Record:

- the four connected participants and their roles
- the Coordinator's bounded plan
- the Builder's scoped change
- the Verifier's first check, including a failure or veto if it occurs
- the Builder's evidence-based revision
- the Critic's independent challenge
- the human owner's decision
- the finished service running from its clean container

Do not record secrets, private API keys, real user data, or unreleased confidential material. Pause the recording while entering credentials.

## 6. Export the room at kickoff

The organizer-provided harness and the written stage specification are released at kickoff. The exact export command and options are authoritative; do not invent flags or fabricate an export.

Once the official harness is available, run from the repository root:

```bash
cd /home/wesley/Desktop/FactoryProof
harness --help
harness check
harness export-room
```

Keep the organizer's original output unchanged. Save the official room export in `evidence/`; the local preflight expects the conventional copy at:

```text
evidence/band-room-export.json
```

If the official command emits a different filename or archive format, preserve it and update the local check to match the organizer's format. The repository's `./harness export-room` command is only a local preflight and cannot create official BAND evidence.

## 7. Validate the evidence package

Run:

```bash
cd /home/wesley/Desktop/FactoryProof
./harness check --strict
```

Before submission, the strict check should have no blockers. It also requires the external items listed in `evidence/README.md`:

- official BAND room export
- room-and-service demo video
- public repository URL
- deployed clean-container application URL
- finalized links in `evidence/submission_links.md`

Cover and slide files are already generated in `evidence/`. The local rehearsal JSON is useful for development but is not a substitute for the BAND export.

## 8. Troubleshooting

**Band Desktop cannot find the CLI:** use the install/repair action in Band Desktop, then click Recheck.

**No messages arrive:** confirm the participant is in the room, the agent uses a distinct identity, the plugin is installed, Claude Code was restarted, and readiness is green.

**Agent went quiet:** check for duplicate processes using the same agent ID; keep one process per identity.

**Only a transcript exists:** add a dependent `@mention` handoff, a runtime recruitment, or a critic veto. Agents posting unrelated status messages does not demonstrate meaningful use.

**Export command not found:** the official harness has not been released or installed yet. Wait for the organizer's instructions; never hand-create a room export.

## 9. Required explanation in the submission

Use `band_agents/room_protocol.md` to explain:

- the crew and each seat's single job
- who talks to whom through `@mentions`
- the end-to-end flow
- what breaks when the room is removed

Official references: [BAND Desktop](https://docs.band.ai/jam), [BAND Hacker Guide](https://www.band.ai/hacker-guide), [Dark Factory event](https://lablab.ai/ai-hackathons/wearedevelopers-hackathon).
