# Troubleshooting (v0.2.1)

## A01 not recognized
Call:
- `GET http://localhost:8040/model`

This shows the exact IDs loaded.

If an old `plant_model.json` is overriding defaults via the `opc_models` volume, reset volumes:
```bash
docker compose down
docker volume ls
# remove the two volumes for this project:
docker volume rm <project>_opc_models <project>_opc_certs
docker compose up -d --build
```

## Historian tables are empty
1) Ensure tables exist (run init SQL once).
2) Check:
- `GET http://localhost:8040/historian/status` → see `last_error`
3) Check logs:
```bash
docker logs -f <opc-studio-container>
```

## Windows PowerShell curl
PowerShell `curl` is not real curl. Use `curl.exe`:

```powershell
curl.exe -X POST http://localhost:8040/scenario/apply `
  -H "Content-Type: application/json" `
  -d "{\"line\":\"A01\",\"station\":\"ST17\",\"event\":\"MaterialShortage\",\"duration_min\":30,\"impact\":{\"availability\":-0.4,\"alarms\":[\"MAT_SHORT\"]}}"
```

Or `Invoke-RestMethod`:

```powershell
$body = @{
  line="A01"; station="ST17"; event="MaterialShortage"; duration_min=30;
  impact=@{ availability=-0.4; alarms=@("MAT_SHORT") }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri http://localhost:8040/scenario/apply -ContentType "application/json" -Body $body
```
