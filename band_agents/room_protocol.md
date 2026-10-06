# BAND room protocol

See `../BAND_ROOM_EXPORT_RUNBOOK.md` for the complete Desktop, recording, and official export procedure.

Use one BAND Desktop room for the complete case. Keep the room visible in the recording.

1. Create the room and add the coordinator, builder, verifier, and critic as Remote Agents.
2. Turn on tool and execution events.
3. Send the Pocketful task from `pocketful_task.md` to the coordinator.
4. Require the coordinator to mention the builder with the bounded contract.
5. Require the builder to mention the verifier with changed files and checks.
6. Require the verifier to preserve failed evidence and mention the critic after the required checks.
7. Require the critic to post either `BLOCKED` or a clear recommendation and mention the human owner.
8. Record the human owner's promotion decision in the room.
9. Export the room with the official `harness export-room` command.

The room must show dependent work: removing a handoff, verifier veto, or critic gate changes the outcome. Independent status messages alone do not satisfy the meaningful-use requirement.
