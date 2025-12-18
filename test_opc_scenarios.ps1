# OPC Studio Scenario Testing Script
# Run these commands to test different what-if scenarios

Write-Host "OPC Studio Scenario Testing" -ForegroundColor Cyan
Write-Host ""

# Base URL
$baseUrl = "http://localhost:8040"

# Function to inject a scenario
function Invoke-Scenario {
    param(
        [string]$ScenarioType,
        [string]$TargetLine,
        [string]$TargetStation = $null,
        [int]$DurationMinutes = 15,
        [string]$Severity = "medium"
    )
    
    $body = @{
        scenario_type = $ScenarioType
        target_line = $TargetLine
        duration_minutes = $DurationMinutes
        severity = $Severity
        parameters = @{}
    }
    
    if ($TargetStation) {
        $body.target_station = $TargetStation
    }
    
    $json = $body | ConvertTo-Json
    
    Write-Host "Injecting: $ScenarioType on $TargetLine" -ForegroundColor Yellow
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/api/scenarios/inject" -Method Post -Body $json -ContentType "application/json"
        Write-Host "SUCCESS - Scenario ID: $($result.scenario_id)" -ForegroundColor Green
        return $result
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
    }
}

# Function to get active scenarios
function Get-ActiveScenarios {
    Write-Host "Active Scenarios:" -ForegroundColor Cyan
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/api/scenarios/active" -Method Get
        $result.active_scenarios | Format-Table scenario_id, scenario_type, target_line, severity, time_remaining_minutes -AutoSize
        return $result
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
    }
}

# Function to stop a scenario
function Stop-Scenario {
    param([string]$ScenarioId)
    
    Write-Host "Stopping scenario: $ScenarioId" -ForegroundColor Yellow
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/api/scenarios/$ScenarioId" -Method Delete
        Write-Host "SUCCESS - Stopped: $($result.message)" -ForegroundColor Green
        return $result
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
    }
}

# Function to read OPC node value
function Get-OPCNodeValue {
    param([string]$NodePath)
    
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/api/opc/read/$NodePath" -Method Get
        return $result
    } catch {
        Write-Host "ERROR reading $NodePath : $_" -ForegroundColor Red
    }
}

# Function to get OPC status
function Get-OPCStatus {
    Write-Host "OPC Studio Status:" -ForegroundColor Cyan
    try {
        $result = Invoke-RestMethod -Uri "$baseUrl/api/status" -Method Get
        $result | ConvertTo-Json -Depth 4
        return $result
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
    }
}

# ==================== Example Usage ====================

Write-Host "Available commands:" -ForegroundColor Green
Write-Host ""
Write-Host "  Get-OPCStatus                          # View OPC Studio status"
Write-Host "  Get-ActiveScenarios                    # List active scenarios"
Write-Host "  Get-OPCNodeValue 'Plant.LINE_A.OEE'   # Read OPC node value"
Write-Host ""
Write-Host "Scenario injection examples:" -ForegroundColor Green
Write-Host ""
Write-Host "  # Equipment Failure (high severity, specific station)" -ForegroundColor Gray
Write-Host '  Invoke-Scenario -ScenarioType "EquipmentFailure" -TargetLine "LINE_A" -TargetStation "ST_A2" -DurationMinutes 20 -Severity "high"'
Write-Host ""
Write-Host "  # Quality Issue (medium severity, entire line)" -ForegroundColor Gray
Write-Host '  Invoke-Scenario -ScenarioType "QualityIssue" -TargetLine "LINE_B" -DurationMinutes 15 -Severity "medium"'
Write-Host ""
Write-Host "  # Material Shortage (low severity)" -ForegroundColor Gray
Write-Host '  Invoke-Scenario -ScenarioType "MaterialShortage" -TargetLine "LINE_C" -DurationMinutes 30 -Severity "low"'
Write-Host ""
Write-Host "  # Process Slowdown" -ForegroundColor Gray
Write-Host '  Invoke-Scenario -ScenarioType "ProcessSlowdown" -TargetLine "LINE_A" -DurationMinutes 25 -Severity "medium"'
Write-Host ""
Write-Host "  # Maintenance Required" -ForegroundColor Gray
Write-Host '  Invoke-Scenario -ScenarioType "MaintenanceRequired" -TargetLine "LINE_B" -TargetStation "ST_B3" -DurationMinutes 40 -Severity "medium"'
Write-Host ""
Write-Host "  # Stop a scenario" -ForegroundColor Gray
Write-Host '  Stop-Scenario -ScenarioId "ae0f6b01"'
Write-Host ""

# ==================== Quick Test Suite ====================

Write-Host "Run quick test? (Y/N): " -NoNewline -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Running Quick Test Suite..." -ForegroundColor Cyan
    Write-Host ""
    
    # Test 1: Get status
    Write-Host "Test 1: Get OPC Status" -ForegroundColor Magenta
    Get-OPCStatus
    Write-Host ""
    Start-Sleep -Seconds 2
    
    # Test 2: Read baseline OEE
    Write-Host "Test 2: Read Baseline OEE for LINE_A" -ForegroundColor Magenta
    $baseline = Get-OPCNodeValue "Plant.LINE_A.OEE"
    Write-Host "Baseline OEE: $($baseline.value)" -ForegroundColor Cyan
    Write-Host ""
    Start-Sleep -Seconds 2
    
    # Test 3: Inject Equipment Failure
    Write-Host "Test 3: Inject Equipment Failure on LINE_A" -ForegroundColor Magenta
    $scenario = Invoke-Scenario -ScenarioType "EquipmentFailure" -TargetLine "LINE_A" -TargetStation "ST_A2" -DurationMinutes 5 -Severity "high"
    Write-Host ""
    Start-Sleep -Seconds 3
    
    # Test 4: Read impacted OEE
    Write-Host "Test 4: Read Impacted OEE for LINE_A (should be lower)" -ForegroundColor Magenta
    $impacted = Get-OPCNodeValue "Plant.LINE_A.OEE"
    Write-Host "Impacted OEE: $($impacted.value)" -ForegroundColor Cyan
    Write-Host "Impact: $(($baseline.value - $impacted.value) * 100)% reduction" -ForegroundColor Red
    Write-Host ""
    Start-Sleep -Seconds 2
    
    # Test 5: List active scenarios
    Write-Host "Test 5: List Active Scenarios" -ForegroundColor Magenta
    Get-ActiveScenarios
    Write-Host ""
    
    # Test 6: Stop scenario
    if ($scenario) {
        Write-Host "Test 6: Stop Scenario" -ForegroundColor Magenta
        Stop-Scenario -ScenarioId $scenario.scenario_id
        Write-Host ""
        Start-Sleep -Seconds 2
        
        # Test 7: Verify recovery
        Write-Host "Test 7: Verify OEE Recovery" -ForegroundColor Magenta
        $recovered = Get-OPCNodeValue "Plant.LINE_A.OEE"
        Write-Host "Recovered OEE: $($recovered.value)" -ForegroundColor Cyan
        Write-Host ""
    }
    
    Write-Host "Test Suite Complete!" -ForegroundColor Green
}

Write-Host ""
Write-Host "For more info, see: http://localhost:8040/docs" -ForegroundColor Cyan
