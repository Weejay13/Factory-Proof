# Stage 1 — Pocketful JSON API

This folder is the complete stage-1 service for the Pocketful track. It provides wallet creation and transfer endpoints with explicit validation and integer-cent accounting.

The official kickoff specification is authoritative for final endpoint names, response shapes, and error codes. Replace this reference behavior with the released harness contract at kickoff while keeping the service independently runnable.

```bash
python3 app.py --host 127.0.0.1 --port 8080
```

The service is intentionally self-contained and makes no outbound network calls.
