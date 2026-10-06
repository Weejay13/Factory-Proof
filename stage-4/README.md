# Stage 4 — Pocketful refunds

This stage extends the same wallet domain with idempotent refunds. A refund reverses the original transfer exactly once, preserves integer-cent accounting, and appends an audit event.

```bash
python3 app.py --host 127.0.0.1 --port 8080
```

The official kickoff specification remains authoritative for the final extension contract.
