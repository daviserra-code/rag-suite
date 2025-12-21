# QA Testing Package

This directory contains the production-safe QA test plan and automated smoke test scripts for Shopfloor Copilot + OPC Studio.

## Contents

1. **[TEST_PLAN.md](TEST_PLAN.md)** - Comprehensive manual test plan covering 6 layers:
   - Layer 0: Runtime & Service Health
   - Layer 1: OPC Explorer (Sprint 1)
   - Layer 2: Semantic Mapping (Sprint 2)
   - Layer 3: Phase B Unified Runtime Views
   - Layer 4: Diagnostics Explainability (Sprint 3)
   - Layer 5: Regression Testing

2. **[../scripts/SMOKE_TEST.ps1](../scripts/SMOKE_TEST.ps1)** - Windows PowerShell smoke test script
3. **[../scripts/SMOKE_TEST.sh](../scripts/SMOKE_TEST.sh)** - Linux/macOS bash smoke test script

## Quick Start

### Windows (PowerShell)
```powershell
# From repository root
powershell -ExecutionPolicy Bypass -File .\scripts\SMOKE_TEST.ps1
```

### Linux/macOS (Bash)
```bash
# From repository root
chmod +x scripts/SMOKE_TEST.sh
./scripts/SMOKE_TEST.sh
```

## Configuration

All scripts support environment variable overrides:

- `SHOPFLOOR_API_URL` - Default: `http://localhost:8010`
- `OPC_STUDIO_URL` - Default: `http://localhost:8040`
- `POSTGRES_HOST` - Default: `localhost`
- `POSTGRES_PORT` - Default: `5432`
- `POSTGRES_DB` - Default: `ragdb`
- `POSTGRES_USER` - Default: `postgres`
- `POSTGRES_PASSWORD` - Default: `postgres`

### Example with Custom Ports
```powershell
# Windows
$env:SHOPFLOOR_API_URL = "http://localhost:8015"
$env:OPC_STUDIO_URL = "http://localhost:8045"
.\scripts\SMOKE_TEST.ps1
```

```bash
# Linux/macOS
export SHOPFLOOR_API_URL="http://localhost:8015"
export OPC_STUDIO_URL="http://localhost:8045"
./scripts/SMOKE_TEST.sh
```

## Test Output

Scripts provide color-coded output:
- 🟢 **[PASS]** - Test passed successfully
- 🔴 **[FAIL]** - Critical failure detected
- 🟡 **[WARN]** - Non-critical issue or optional component unavailable
- 🔵 **[INFO]** - Informational message

## Exit Codes

- `0` - All tests passed (may have warnings)
- `1` - One or more critical failures

## Requirements

### Minimum (both scripts)
- Docker & Docker Compose (for container checks)
- `curl` or PowerShell web cmdlets (for HTTP checks)

### Optional (enhanced validation)
- **jq** (JSON parsing) - Available via `apt install jq`, `brew install jq`, or `choco install jq`
- **psql** (PostgreSQL client) - Available via PostgreSQL installation

## Typical Test Results

### Healthy System
```
======================================
Test Summary
======================================
PASS: 18
FAIL: 0
WARN: 0
======================================
SMOKE TEST PASSED - All checks successful!
```

### System with OPC Disconnected
```
======================================
Test Summary
======================================
PASS: 12
FAIL: 0
WARN: 6
======================================
SMOKE TEST PASSED WITH WARNINGS - 6 warnings
```

### Critical Failure
```
======================================
Test Summary
======================================
PASS: 5
FAIL: 3
WARN: 2
======================================
SMOKE TEST FAILED - 3 critical failures
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Smoke Tests
  run: |
    docker compose up -d
    sleep 30  # Wait for services to start
    ./scripts/SMOKE_TEST.sh
```

### Jenkins Example
```groovy
stage('Smoke Tests') {
    steps {
        sh 'docker compose up -d'
        sh 'sleep 30'
        sh './scripts/SMOKE_TEST.sh'
    }
}
```

## Troubleshooting

### PowerShell Execution Policy Error
```powershell
# Run with bypass flag
powershell -ExecutionPolicy Bypass -File .\scripts\SMOKE_TEST.ps1

# OR set policy (requires admin)
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Script Not Executable (Linux/macOS)
```bash
chmod +x scripts/SMOKE_TEST.sh
```

### Database Tests Skipped
Install PostgreSQL client:
- **Ubuntu/Debian:** `sudo apt install postgresql-client`
- **macOS:** `brew install postgresql`
- **Windows:** Download from [postgresql.org](https://www.postgresql.org/download/windows/)

## Safety Guarantees

✅ **Read-Only Operations** - No destructive database operations  
✅ **No Logic Changes** - Scripts only validate, never modify  
✅ **Production Safe** - Can run on live systems without risk  
✅ **Configurable** - All URLs/ports overridable via environment  

## Support

For issues or questions:
1. Check [TEST_PLAN.md](TEST_PLAN.md) for detailed test procedures
2. Review service logs: `docker compose logs -f <service>`
3. Verify configuration in `.env` or `.env.prod`

---

**Version:** 1.0  
**Last Updated:** December 21, 2025  
**Maintainer:** Shopfloor Copilot Team
