# Stage 3 — Pocketful concurrency control

This stage adds an atomic transfer path, idempotency-key replay protection, fingerprint mismatch rejection, and an audit event stream. The lock protects the complete check-and-act sequence in the reference service.

```bash
python3 app.py --host 127.0.0.1 --port 8080
```

The official harness may require a database-level transaction or a different persistence contract. Replace the in-memory store with the specified persistence layer after the kickoff SPEC is released.
