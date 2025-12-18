# OPC Studio v0.2 — Historian Bridge

Adds a minimal **Historian Bridge** that writes OPC-derived samples and events to Postgres.

## Ports
- REST API: `8040`
- OPC UA: `4840` (endpoint: `opc.tcp://<host>:4840/shopfloor/opc-studio`)

## REST endpoints
- `GET /health`
- `GET /snapshot`
- `POST /scenario/apply`
- `GET /historian/status`

## Historian tables (Postgres)
Run `sql/init_opc_historian.sql` once (see instructions below).

### Apply DB init
```bash
docker compose up -d --build
docker compose ps
# then run init SQL:
docker exec -i <postgres_container_name> psql -U postgres -d ragdb < sql/init_opc_historian.sql
```

## Environment
- `DATABASE_URL`
- `HISTORIAN_ENABLED=true|false`
- `HISTORIAN_INTERVAL_S=5`
