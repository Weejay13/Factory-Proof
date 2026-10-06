from __future__ import annotations

import copy
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .acceptance import demo_sources, make_patch, verify_candidate
from .models import Agent, Artifact, Event, Run, now_iso


DEFAULT_TASK = "Build a Pocketful-style wallet transfer service. Retries must return the original result, concurrent transfers must not move money twice, and malformed or insufficient transfers must be rejected."


class FactoryRunner:
    def __init__(self, root: Path, delay: float = 0.0) -> None:
        self.root = Path(root)
        self.delay = max(0.0, float(delay))
        self.runs_dir = self.root / "var" / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, Run] = {}
        self._latest: str | None = None
        self._lock = threading.RLock()

    def start_run(self, task: str = DEFAULT_TASK, mode: str = "offline") -> dict[str, Any]:
        clean_task = task.strip() or DEFAULT_TASK
        run_id = self._new_run_id()
        created = now_iso()
        run = Run(
            id=run_id,
            task=clean_task,
            mode=mode,
            status="queued",
            created_at=created,
            updated_at=created,
            agents=[
                Agent("Case Coordinator", "coordinator", "Routes work and owns escalation"),
                Agent("Plan Architect", "architect", "Turns the case into a bounded build plan"),
                Agent("Patch Builder", "builder", "Implements only the approved interface"),
                Agent("Quality Verifier", "verifier", "Runs public and sealed acceptance checks"),
                Agent("Release Critic", "critic", "Challenges the evidence and blocks unsupported verdicts"),
                Agent("Human Owner", "human", "Owns the final promotion decision"),
            ],
            metrics={
                "public_tests": "—",
                "sealed_tests": "—",
                "patch_attempts": 0,
                "human_approvals": 0,
                "band_messages": 0,
                "blocked_checks": 0,
                "elapsed_ms": 0,
            },
        )
        with self._lock:
            self._runs[run_id] = run
            self._latest = run_id
        worker = threading.Thread(target=self._execute, args=(run_id,), daemon=True)
        worker.start()
        return self.get_run(run_id) or {}

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(run_id)
            return copy.deepcopy(run.to_dict()) if run else None

    def latest(self) -> dict[str, Any] | None:
        with self._lock:
            run_id = self._latest
        return self.get_run(run_id) if run_id else None

    def approve(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return None
            if run.status != "awaiting_human":
                return self.get_run(run_id)
            self._set_status(run_id, "shipped")
            run.human_gate = "approved"
            run.metrics["human_approvals"] = 1
            self._emit(
                run_id,
                actor="Human Owner",
                role="human",
                kind="approval",
                message="Approved the release packet. The case is ready to ship.",
                recipient=None,
                artifact="release-report.json",
                level="success",
            )
            run.report = self._build_report(run)
            self._persist(run_id)
            return self.get_run(run_id)

    def _execute(self, run_id: str) -> None:
        started = time.perf_counter()
        try:
            with self._lock:
                run = self._runs[run_id]
                run.metrics["elapsed_ms"] = 0
            self._pause()
            self._set_status(run_id, "planning")
            self._emit(
                run_id,
                actor="Case Coordinator",
                role="coordinator",
                kind="signal",
                message="Case received. Opening a bounded factory room and requesting a plan.",
                recipient="Plan Architect",
                execution=True,
            )
            self._pause()
            self._emit(
                run_id,
                actor="Plan Architect",
                role="architect",
                kind="handoff",
                message="Plan accepted: isolate the wallet service, preserve integer cents, and keep retries from moving money twice.",
                recipient="Case Coordinator",
                artifact="build-plan.md",
            )
            self._add_artifact(
                run_id,
                "build-plan.md",
                "plan",
                "Bounded implementation plan produced from the case brief.",
                "# Build plan\n\n- Scope: wallet transfer service only\n- Contract: retries return the original transfer and money never moves twice\n- Gate: public tests plus sealed acceptance tests\n- Promotion: human approval required\n",
            )
            self._pause()
            self._emit(
                run_id,
                actor="Case Coordinator",
                role="coordinator",
                kind="recruit",
                message="band_lookup_peers found Patch Builder and Quality Verifier; recruiting both for this case.",
                recipient="Patch Builder",
                execution=True,
            )
            self._emit(
                run_id,
                actor="Case Coordinator",
                role="coordinator",
                kind="handoff",
                message="@Patch Builder implement the bounded contract. @Quality Verifier prepare sealed checks before reviewing the patch.",
                recipient="Patch Builder",
                execution=True,
            )
            with self._lock:
                run = self._runs[run_id]
                run.metrics["band_messages"] += 2
                run.metrics["patch_attempts"] = 1
            self._pause()
            self._set_status(run_id, "implementing")
            self._emit(
                run_id,
                actor="Patch Builder",
                role="builder",
                kind="tool_call",
                message="Applied a first minimal implementation and sent it to the verifier.",
                recipient="Quality Verifier",
                artifact="builder-v1.diff",
                execution=True,
            )
            sources = demo_sources()
            self._add_artifact(
                run_id,
                "builder-v1.diff",
                "diff",
                "First candidate patch; it passes visible checks but fails the sealed idempotency check.",
                make_patch(sources["baseline"], sources["v1"]),
            )
            first = verify_candidate(sources["v1"])
            self._add_artifact(
                run_id,
                "verifier-v1.json",
                "verification",
                "Verifier evidence for the first candidate.",
                json.dumps(first, indent=2),
            )
            with self._lock:
                run = self._runs[run_id]
                run.metrics["public_tests"] = "pass"
                run.metrics["sealed_tests"] = "fail"
                run.metrics["blocked_checks"] = 1
            self._emit(
                run_id,
                actor="Quality Verifier",
                role="verifier",
                kind="veto",
                message="BLOCKED: sealed acceptance check failed. A repeated idempotency key moved money a second time.",
                recipient="Patch Builder",
                artifact="verifier-v1.json",
                level="danger",
                execution=True,
            )
            self._pause()
            self._set_status(run_id, "revising")
            self._emit(
                run_id,
                actor="Patch Builder",
                role="builder",
                kind="handoff",
                message="Verifier evidence received. Adding an explicit idempotency guard and rerunning the sealed contract.",
                recipient="Quality Verifier",
                execution=True,
            )
            with self._lock:
                run = self._runs[run_id]
                run.metrics["patch_attempts"] = 2
            self._pause()
            self._emit(
                run_id,
                actor="Patch Builder",
                role="builder",
                kind="tool_call",
                message="Revision complete. The patch returns the original transfer without moving money again.",
                recipient="Quality Verifier",
                artifact="builder-v2.diff",
                execution=True,
            )
            self._add_artifact(
                run_id,
                "builder-v2.diff",
                "diff",
                "Second candidate patch with the explicit idempotency guard.",
                make_patch(sources["baseline"], sources["v2"]),
            )
            second = verify_candidate(sources["v2"])
            self._add_artifact(
                run_id,
                "verifier-v2.json",
                "verification",
                "Verifier evidence for the revised candidate.",
                json.dumps(second, indent=2),
            )
            with self._lock:
                run = self._runs[run_id]
                run.metrics["public_tests"] = "pass" if second["public"]["passed"] else "fail"
                run.metrics["sealed_tests"] = "pass" if second["sealed"]["passed"] else "fail"
            if not second["public"]["passed"] or not second["sealed"]["passed"]:
                self._set_status(run_id, "failed")
                self._emit(
                    run_id,
                    actor="Quality Verifier",
                    role="verifier",
                    kind="veto",
                    message="BLOCKED: the revised candidate still fails the release contract.",
                    recipient="Release Critic",
                    artifact="verifier-v2.json",
                    level="danger",
                )
                self._finish(run_id, started)
                return
            self._pause()
            self._set_status(run_id, "reviewing")
            self._emit(
                run_id,
                actor="Quality Verifier",
                role="verifier",
                kind="handoff",
                message="Public and sealed checks are green. Sending the evidence packet to the Release Critic.",
                recipient="Release Critic",
                artifact="verifier-v2.json",
                execution=True,
            )
            self._pause()
            self._emit(
                run_id,
                actor="Release Critic",
                role="critic",
                kind="verdict",
                message="Evidence is sufficient: the patch is scoped, verified, and reversible. Recommend promotion.",
                recipient="Human Owner",
                artifact="release-report.json",
                level="success",
                execution=True,
            )
            self._add_artifact(
                run_id,
                "release-report.json",
                "report",
                "Release gate packet awaiting human promotion.",
                json.dumps({"public": second["public"], "sealed": second["sealed"], "recommendation": "promote"}, indent=2),
            )
            self._set_status(run_id, "awaiting_human")
            with self._lock:
                run = self._runs[run_id]
                run.human_gate = "pending"
            self._emit(
                run_id,
                actor="Case Coordinator",
                role="coordinator",
                kind="gate",
                message="Human gate reached. No agent can promote the case without an owner decision.",
                recipient="Human Owner",
                artifact="release-report.json",
                level="warning",
            )
            self._finish(run_id, started)
        except Exception as error:
            with self._lock:
                run = self._runs.get(run_id)
                if run is not None:
                    run.status = "failed"
                    run.updated_at = now_iso()
                    self._emit_locked(
                        run,
                        actor="Case Coordinator",
                        role="coordinator",
                        kind="error",
                        message=f"Factory run failed safely: {error}",
                        level="danger",
                    )
            self._finish(run_id, started)

    def _finish(self, run_id: str, started: float) -> None:
        with self._lock:
            run = self._runs[run_id]
            run.metrics["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
            run.updated_at = now_iso()
            run.report = self._build_report(run)
        self._persist(run_id)

    def _build_report(self, run: Run) -> dict[str, Any]:
        return {
            "run_id": run.id,
            "task": run.task,
            "mode": run.mode,
            "status": run.status,
            "human_gate": run.human_gate,
            "metrics": run.metrics,
            "artifacts": sorted(run.artifacts),
            "recommendation": "promote" if run.human_gate == "approved" else "awaiting_human",
        }

    def _set_status(self, run_id: str, status: str) -> None:
        with self._lock:
            run = self._runs[run_id]
            run.status = status
            run.updated_at = now_iso()

    def _add_artifact(self, run_id: str, name: str, kind: str, description: str, content: str) -> None:
        with self._lock:
            run = self._runs[run_id]
            run.artifacts[name] = Artifact(name, kind, description, content)
            run.updated_at = now_iso()

    def _emit(
        self,
        run_id: str,
        actor: str,
        role: str,
        kind: str,
        message: str,
        recipient: str | None = None,
        artifact: str | None = None,
        level: str = "info",
        execution: bool = False,
    ) -> None:
        with self._lock:
            run = self._runs[run_id]
            self._emit_locked(run, actor, role, kind, message, recipient, artifact, level, execution)

    def _emit_locked(
        self,
        run: Run,
        actor: str,
        role: str,
        kind: str,
        message: str,
        recipient: str | None = None,
        artifact: str | None = None,
        level: str = "info",
        execution: bool = False,
    ) -> None:
        event = Event(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            actor=actor,
            role=role,
            kind=kind,
            message=message,
            recipient=recipient,
            artifact=artifact,
            level=level,
            execution=execution,
        )
        run.events.append(event)
        run.updated_at = now_iso()
        for agent in run.agents:
            if agent.name == actor:
                agent.last_action = message
                if kind in {"veto", "error"}:
                    agent.status = "blocked"
                elif kind in {"verdict", "approval"}:
                    agent.status = "approved"
                else:
                    agent.status = "working"
            if recipient and agent.name == recipient and agent.status == "waiting":
                agent.status = "working"

    def _persist(self, run_id: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return
            payload = run.to_dict()
        path = self.runs_dir / f"{run_id}.json"
        temporary = path.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            temporary.replace(path)
        except OSError:
            return

    @staticmethod
    def _new_run_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"run_{stamp}_{uuid.uuid4().hex[:6]}"

    def _pause(self) -> None:
        if self.delay:
            time.sleep(self.delay)
