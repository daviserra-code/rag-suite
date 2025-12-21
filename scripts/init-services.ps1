# ============================================================================
# init-services.ps1 - Initialize Shopfloor Copilot Services
# ============================================================================
# Purpose: Configure OPC Studio and load semantic mappings after startup
# Usage: .\scripts\init-services.ps1
# Run this after: docker compose up -d
# ============================================================================

param(
    [string]$OpcStudioUrl = $(if ($env:OPC_STUDIO_URL) { $env:OPC_STUDIO_URL } else { "http://localhost:8040" }),
    [string]$OpcDemoEndpoint = "opc.tcp://opc-demo:4850",
    [int]$MaxRetries = 30,
    [int]$RetryDelay = 2
)

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Shopfloor Copilot Service Initialization" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

function Wait-ForService {
    param(
        [string]$Url,
        [string]$ServiceName
    )
    
    Write-Host "Waiting for $ServiceName to be ready..." -ForegroundColor Yellow
    $retries = 0
    
    while ($retries -lt $MaxRetries) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "[OK] $ServiceName is ready" -ForegroundColor Green
                return $true
            }
        } catch {
            $retries++
            if ($retries -lt $MaxRetries) {
                Write-Host "  Waiting... ($retries/$MaxRetries)" -ForegroundColor Gray
                Start-Sleep -Seconds $RetryDelay
            }
        }
    }
    
    Write-Host "[FAIL] $ServiceName failed to start after $MaxRetries attempts" -ForegroundColor Red
    return $false
}

# ----------------------------------------------------------------------------
# Step 1: Wait for services to be ready
# ----------------------------------------------------------------------------
Write-Host "`n[Step 1] Waiting for services..." -ForegroundColor Yellow

if (-not (Wait-ForService -Url "$OpcStudioUrl/health" -ServiceName "OPC Studio")) {
    Write-Host "`nFailed to initialize: OPC Studio not available" -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------------------
# Step 2: Verify Plant Model
# ----------------------------------------------------------------------------
Write-Host "`n[Step 2] Verifying plant model..." -ForegroundColor Yellow

try {
    $model = Invoke-RestMethod -Uri "$OpcStudioUrl/model" `
        -Method Get `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    if ($model.ok -and $model.model) {
        Write-Host "[OK] Plant model loaded" -ForegroundColor Green
        Write-Host "  Lines: $($model.model.lines.Count)" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] Plant model exists but no data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Failed to retrieve plant model: $($_.Exception.Message)" -ForegroundColor Red
}

# ----------------------------------------------------------------------------
# Step 3: Verify Semantic Snapshot
# ----------------------------------------------------------------------------
Write-Host "`n[Step 3] Verifying semantic snapshot..." -ForegroundColor Yellow

try {
    $snapshot = Invoke-RestMethod -Uri "$OpcStudioUrl/snapshot" `
        -Method Get `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    if ($snapshot.ok -and $snapshot.data) {
        Write-Host "[OK] Semantic snapshot available" -ForegroundColor Green
        Write-Host "  Plant: $($snapshot.data.plant_name)" -ForegroundColor Gray
        if ($snapshot.data.lines) {
            $lineCount = ($snapshot.data.lines | Measure-Object).Count
            Write-Host "  Lines: $lineCount" -ForegroundColor Gray
        }
    } else {
        Write-Host "[WARN] Semantic snapshot exists but no plant data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Failed to retrieve semantic snapshot: $($_.Exception.Message)" -ForegroundColor Red
}

# ----------------------------------------------------------------------------
# Step 4: Check Historian Status
# ----------------------------------------------------------------------------
Write-Host "`n[Step 4] Checking historian status..." -ForegroundColor Yellow

try {
    $historian = Invoke-RestMethod -Uri "$OpcStudioUrl/historian/status" `
        -Method Get `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    if ($historian.ok) {
        Write-Host "[OK] Historian status retrieved" -ForegroundColor Green
        Write-Host "  Enabled: $($historian.enabled)" -ForegroundColor Gray
        Write-Host "  Interval: $($historian.interval_s)s" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] Historian status check returned no data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Failed to check historian: $($_.Exception.Message)" -ForegroundColor Red
}

# ----------------------------------------------------------------------------
# Step 5: Test Scenario Engine
# ----------------------------------------------------------------------------
Write-Host "`n[Step 5] Testing scenario engine..." -ForegroundColor Yellow

try {
    $taxonomy = Invoke-RestMethod -Uri "$OpcStudioUrl/scenario/taxonomy" `
        -Method Get `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    if ($taxonomy.ok -and $taxonomy.taxonomy) {
        Write-Host "[OK] Scenario engine operational" -ForegroundColor Green
        $eventCount = ($taxonomy.taxonomy.events | Measure-Object).Count
        Write-Host "  Event types: $eventCount" -ForegroundColor Gray
    } else {
        Write-Host "[WARN] Scenario engine returned no data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[FAIL] Failed to query scenario engine: $($_.Exception.Message)" -ForegroundColor Red
}

# ----------------------------------------------------------------------------
# Step 6: Check Ollama Model
# ----------------------------------------------------------------------------
Write-Host "`n[Step 6] Checking Ollama model..." -ForegroundColor Yellow

try {
    $ollamaModels = docker exec shopfloor-ollama ollama list 2>&1
    if ($LASTEXITCODE -eq 0) {
        $modelLines = $ollamaModels | Select-String -Pattern "llama" 
        if ($modelLines) {
            Write-Host "[OK] Ollama models installed:" -ForegroundColor Green
            foreach ($line in $modelLines) {
                Write-Host "  $line" -ForegroundColor Gray
            }
        } else {
            Write-Host "[WARN] No Llama models found in Ollama" -ForegroundColor Yellow
            Write-Host "  Run: docker exec shopfloor-ollama ollama pull llama3.2:3b" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[WARN] Could not check Ollama (container may not be running)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] Could not check Ollama: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ----------------------------------------------------------------------------
# Step 7: Check PostgreSQL Client (Optional)
# ----------------------------------------------------------------------------
Write-Host "`n[Step 7] Checking PostgreSQL client..." -ForegroundColor Yellow

$psqlAvailable = Get-Command psql -ErrorAction SilentlyContinue
if ($psqlAvailable) {
    Write-Host "[OK] PostgreSQL client (psql) is installed" -ForegroundColor Green
} else {
    Write-Host "[WARN] PostgreSQL client (psql) not found" -ForegroundColor Yellow
    Write-Host "  This is optional. Install with: choco install postgresql" -ForegroundColor Gray
    Write-Host "  Or use Docker: docker exec shopfloor-postgres psql -U postgres -d ragdb" -ForegroundColor Gray
}

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Initialization Complete!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "`nYour Shopfloor Copilot system is ready." -ForegroundColor Green
Write-Host "Run smoke tests: .\scripts\SMOKE_TEST.ps1`n" -ForegroundColor Cyan
