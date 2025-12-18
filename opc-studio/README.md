# OPC Studio v0.2.1 — Fixes (DB JSON + Better Debug)

Fixes:
- Proper JSONB writes to Postgres (`alarms`, `payload`) using `psycopg.types.json.Json`
- Adds lightweight logging for historian failures (no more silent failures)
- Adds `/model` endpoint to confirm loaded line/station IDs (helps with "A01 not recognized")

## REST endpoints
- `GET /health`
- `GET /model`
- `GET /snapshot`
- `POST /scenario/apply`
- `GET /historian/status`

## Windows PowerShell tip
PowerShell aliases `curl` to `Invoke-WebRequest`. Use `curl.exe` or `Invoke-RestMethod` (see TROUBLESHOOTING.md).
