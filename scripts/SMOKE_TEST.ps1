# ============================================================================
# SMOKE_TEST.ps1 - Shopfloor Copilot Smoke Test Suite (Windows)
# ============================================================================
# Purpose: Quick automated health checks for production deployment
# Usage: .\scripts\SMOKE_TEST.ps1
# Requirements: Docker, PowerShell 5.1+
# Optional: psql (for database checks)
# ============================================================================

param(
    [string]$ShopfloorApiUrl = $env:SHOPFLOOR_API_URL ?? "http://localhost:8010",
    [string]$OpcStudioUrl = $env:OPC_STUDIO_URL ?? "http://localhost:8040",
    [string]$PostgresHost = $env:POSTGRES_HOST ?? "localhost",
    [string]$PostgresPort = $env:POSTGRES_PORT ?? "5432",
    [string]$PostgresDb = $env:POSTGRES_DB ?? "ragdb",
    [string]$PostgresUser = $env:POSTGRES_USER ?? "postgres",
    [string]$PostgresPassword = $env:POSTGRES_PASSWORD ?? "postgres"
)

# Colors for output
function Write-Pass { param($msg) Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }

# Test counters
$script:passCount = 0
$script:failCount = 0
$script:warnCount = 0

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$TestName,
        [int]$ExpectedStatus = 200
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Pass "$TestName (HTTP $($response.StatusCode))"
            $script:passCount++
            return $true
        } else {
            Write-Fail "$TestName (HTTP $($response.StatusCode), expected $ExpectedStatus)"
            $script:failCount++
            return $false
        }
    } catch {
        Write-Fail "$TestName - $($_.Exception.Message)"
        $script:failCount++
        return $false
    }
}

function Test-JsonEndpoint {
    param(
        [string]$Url,
        [string]$TestName,
        [string]$ExpectedKey
    )
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        if ($ExpectedKey -and -not $response.PSObject.Properties[$ExpectedKey]) {
            Write-Fail "$TestName - Missing expected key: $ExpectedKey"
            $script:failCount++
            return $false
        }
        Write-Pass "$TestName"
        $script:passCount++
        return $true
    } catch {
        Write-Fail "$TestName - $($_.Exception.Message)"
        $script:failCount++
        return $false
    }
}

function Test-PostEndpoint {
    param(
        [string]$Url,
        [string]$TestName,
        [hashtable]$Body,
        [int]$ExpectedStatus = 200
    )
    
    try {
        $jsonBody = $Body | ConvertTo-Json -Depth 10
        $response = Invoke-WebRequest -Uri $Url -Method Post -Body $jsonBody -ContentType "application/json" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Pass "$TestName (HTTP $($response.StatusCode))"
            $script:passCount++
            return $true
        } else {
            Write-Fail "$TestName (HTTP $($response.StatusCode), expected $ExpectedStatus)"
            $script:failCount++
            return $false
        }
    } catch {
        Write-Fail "$TestName - $($_.Exception.Message)"
        $script:failCount++
        return $false
    }
}

# ============================================================================
# Main Test Execution
# ============================================================================

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Shopfloor Copilot Smoke Test Suite" -ForegroundColor Cyan
Write-Host "======================================`n" -ForegroundColor Cyan

Write-Info "Configuration:"
Write-Info "  Shopfloor API: $ShopfloorApiUrl"
Write-Info "  OPC Studio:    $OpcStudioUrl"
Write-Info "  Database:      ${PostgresUser}@${PostgresHost}:${PostgresPort}/${PostgresDb}"
Write-Host ""

# ----------------------------------------------------------------------------
# Layer 0: Docker Services
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 0] Docker Services" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

try {
    $containers = docker compose ps --format json 2>$null | ConvertFrom-Json
    if ($containers) {
        $runningCount = ($containers | Where-Object { $_.State -eq "running" }).Count
        $totalCount = $containers.Count
        
        if ($runningCount -eq $totalCount) {
            Write-Pass "Docker Compose: $runningCount/$totalCount containers running"
            $script:passCount++
        } else {
            Write-Warn "Docker Compose: $runningCount/$totalCount containers running"
            $script:warnCount++
            $downContainers = $containers | Where-Object { $_.State -ne "running" }
            foreach ($c in $downContainers) {
                Write-Warn "  - $($c.Service) is $($c.State)"
            }
        }
    } else {
        Write-Fail "Docker Compose: No containers found"
        $script:failCount++
    }
} catch {
    Write-Fail "Docker Compose: Unable to check status - $($_.Exception.Message)"
    $script:failCount++
}

# ----------------------------------------------------------------------------
# Layer 1: Health Endpoints
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 1] Health Endpoints" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

Test-JsonEndpoint -Url "$OpcStudioUrl/health" -TestName "OPC Studio Health" -ExpectedKey "status"
Test-JsonEndpoint -Url "$ShopfloorApiUrl/health" -TestName "Shopfloor API Health" -ExpectedKey "status"
Test-Endpoint -Url "$ShopfloorApiUrl/" -TestName "Shopfloor UI Landing Page"

# ----------------------------------------------------------------------------
# Layer 2: OPC Explorer (Sprint 1)
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 2] OPC Explorer" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

# Test OPC browse endpoint (may fail if not connected, that's OK)
try {
    $browseUrl = "$OpcStudioUrl/opc/browse?nodeId=ns=0;i=85"
    $browseResult = Invoke-RestMethod -Uri $browseUrl -Method Get -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    
    if ($browseResult.children -and $browseResult.children.Count -gt 0) {
        Write-Pass "OPC Browse Root Node ($($browseResult.children.Count) children)"
        $script:passCount++
    } else {
        Write-Warn "OPC Browse returned no children (may not be connected)"
        $script:warnCount++
    }
} catch {
    Write-Warn "OPC Browse - $($_.Exception.Message) (may not be connected)"
    $script:warnCount++
}

# ----------------------------------------------------------------------------
# Layer 3: Semantic Mapping (Sprint 2)
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 3] Semantic Mapping" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

try {
    $snapshotUrl = "$OpcStudioUrl/semantic/snapshot"
    $snapshot = Invoke-RestMethod -Uri $snapshotUrl -Method Get -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    
    if ($snapshot.plant) {
        Write-Pass "Semantic Snapshot Available"
        $script:passCount++
        
        if ($snapshot.lines -and $snapshot.lines.Count -gt 0) {
            Write-Pass "  - Found $($snapshot.lines.Count) mapped lines"
            $script:passCount++
            
            $stationCount = ($snapshot.lines | ForEach-Object { $_.stations.Count } | Measure-Object -Sum).Sum
            if ($stationCount -gt 0) {
                Write-Pass "  - Found $stationCount mapped stations"
                $script:passCount++
            }
        } else {
            Write-Warn "Semantic Snapshot has no mapped lines"
            $script:warnCount++
        }
    } else {
        Write-Fail "Semantic Snapshot missing plant data"
        $script:failCount++
    }
} catch {
    Write-Warn "Semantic Snapshot - $($_.Exception.Message) (may not be configured)"
    $script:warnCount++
}

# ----------------------------------------------------------------------------
# Layer 4: Database Views (Phase B)
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 4] Database Runtime Views" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

# Check if psql is available
$psqlAvailable = Get-Command psql -ErrorAction SilentlyContinue

if ($psqlAvailable) {
    $env:PGPASSWORD = $PostgresPassword
    
    # Test connection
    try {
        $connTest = psql -h $PostgresHost -p $PostgresPort -U $PostgresUser -d $PostgresDb -c "SELECT 1;" -t -A 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Pass "Database Connection"
            $script:passCount++
            
            # Check runtime views exist
            $viewsQuery = "SELECT count(*) FROM information_schema.views WHERE table_schema='public' AND table_name LIKE 'v_runtime%';"
            $viewCount = psql -h $PostgresHost -p $PostgresPort -U $PostgresUser -d $PostgresDb -c $viewsQuery -t -A 2>$null
            
            if ($viewCount -ge 3) {
                Write-Pass "Runtime Views Exist (count: $viewCount)"
                $script:passCount++
            } else {
                Write-Warn "Runtime Views: Expected 3+, found $viewCount"
                $script:warnCount++
            }
            
            # Check recent data
            $dataQuery = "SELECT count(*) FROM oee_line_shift WHERE date >= CURRENT_DATE - INTERVAL '1 day';"
            $dataCount = psql -h $PostgresHost -p $PostgresPort -U $PostgresUser -d $PostgresDb -c $dataQuery -t -A 2>$null
            
            if ($dataCount -gt 50) {
                Write-Pass "Recent OEE Data ($dataCount rows in last 24h)"
                $script:passCount++
            } else {
                Write-Warn "Recent OEE Data: Only $dataCount rows in last 24h (expected >50)"
                $script:warnCount++
            }
        } else {
            Write-Fail "Database Connection Failed"
            $script:failCount++
        }
    } catch {
        Write-Fail "Database Query Error - $($_.Exception.Message)"
        $script:failCount++
    } finally {
        Remove-Item Env:\PGPASSWORD
    }
} else {
    Write-Warn "psql not found - skipping database tests (install PostgreSQL client)"
    $script:warnCount++
}

# ----------------------------------------------------------------------------
# Layer 5: Diagnostics (Sprint 3)
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 5] Diagnostics Explainability" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

$diagBody = @{
    scope = "line"
    id = "A01"
}

try {
    $diagUrl = "$ShopfloorApiUrl/api/diagnostics/explain"
    $diagResponse = Invoke-RestMethod -Uri $diagUrl -Method Post -Body ($diagBody | ConvertTo-Json) -ContentType "application/json" -UseBasicParsing -TimeoutSec 30 -ErrorAction Stop
    
    $requiredFields = @("what", "why", "what_to_do", "checklist", "citations")
    $missingFields = $requiredFields | Where-Object { -not $diagResponse.PSObject.Properties[$_] }
    
    if ($missingFields.Count -eq 0) {
        Write-Pass "Diagnostics Response Structure Complete"
        $script:passCount++
        
        if ($diagResponse.citations -and $diagResponse.citations.Count -gt 0) {
            Write-Pass "  - Citations Present ($($diagResponse.citations.Count) sources)"
            $script:passCount++
        } else {
            Write-Warn "  - No Citations (grounding may be weak)"
            $script:warnCount++
        }
        
        if ($diagResponse.PSObject.Properties["runtime_available"]) {
            $runtimeStatus = if ($diagResponse.runtime_available) { "available" } else { "unavailable" }
            Write-Pass "  - Runtime Status: $runtimeStatus"
            $script:passCount++
        }
    } else {
        Write-Fail "Diagnostics Response Missing Fields: $($missingFields -join ', ')"
        $script:failCount++
    }
} catch {
    Write-Fail "Diagnostics Endpoint - $($_.Exception.Message)"
    $script:failCount++
}

# ----------------------------------------------------------------------------
# Layer 6: Regression - Key Endpoints
# ----------------------------------------------------------------------------
Write-Host "`n[Layer 6] Regression Tests" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow

Test-Endpoint -Url "$ShopfloorApiUrl/kpi-dashboard" -TestName "KPI Dashboard Page"
Test-Endpoint -Url "$ShopfloorApiUrl/live-monitoring" -TestName "Live Monitoring Page"
Test-Endpoint -Url "$ShopfloorApiUrl/opc-explorer" -TestName "OPC Explorer Page"
Test-Endpoint -Url "$ShopfloorApiUrl/diagnostics" -TestName "Diagnostics Hub Page"

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "PASS: $script:passCount" -ForegroundColor Green
Write-Host "FAIL: $script:failCount" -ForegroundColor Red
Write-Host "WARN: $script:warnCount" -ForegroundColor Yellow
Write-Host "======================================`n" -ForegroundColor Cyan

# Exit with failure code if any tests failed
if ($script:failCount -gt 0) {
    Write-Host "SMOKE TEST FAILED - $script:failCount critical failures" -ForegroundColor Red
    exit 1
} elseif ($script:warnCount -gt 0) {
    Write-Host "SMOKE TEST PASSED WITH WARNINGS - $script:warnCount warnings" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "SMOKE TEST PASSED - All checks successful!" -ForegroundColor Green
    exit 0
}
