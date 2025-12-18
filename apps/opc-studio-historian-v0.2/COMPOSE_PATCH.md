# Compose patch (OPC Studio v0.2)

In your main `docker-compose.yml`, ensure `opc-studio` is built from `./opc-studio` and that Postgres is reachable.

Recommended service block:

```yaml
  opc-studio:
    build:
      context: ./opc-studio
      dockerfile: Dockerfile
    env_file: .env
    environment:
      - OPC_STUDIO_HTTP_PORT=8040
      - OPC_UA_PORT=4840
      - OPC_ENDPOINT=opc.tcp://0.0.0.0:4840/shopfloor/opc-studio
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragdb
      - HISTORIAN_ENABLED=true
      - HISTORIAN_INTERVAL_S=5
    depends_on: [postgres]
    ports:
      - "8040:8040"
      - "4840:4840"
    volumes:
      - ./opc-studio:/app
      - opc_certs:/app/certs
      - opc_models:/app/models
    restart: unless-stopped
```

Add volumes if missing:

```yaml
volumes:
  opc_certs: {}
  opc_models: {}
```
