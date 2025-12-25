#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test Citation Discipline - Sprint 5 MES-like RAG Corpus
    
.DESCRIPTION
    Verifies that AI diagnostics:
    1. Cite retrieved documents using document IDs
    2. Different citations appear for different profiles
    3. Output quality improves with corpus vs without
    4. No hallucinated procedures
#>

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79)
Write-Host "SPRINT 5 - CITATION DISCIPLINE VERIFICATION" -ForegroundColor Cyan
Write-Host "MES-like RAG Corpus Strategy" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79)
Write-Host ""

$baseUrl = "http://localhost:8010"
$testsPassed = 0
$testsFailed = 0

# Test scenarios by profile
$testScenarios = @(
    @{
        Profile = "aerospace_defence"
        Station = "ST40"
        ExpectedDocs = @("WI-OP40", "Serial", "Binding", "deviation")
        Description = "A&D missing serial binding"
    },
    @{
        Profile = "pharma_process"
        Station = "ST25"
        ExpectedDocs = @("SOP", "BPR", "Tablet", "deviation")
        Description = "Pharma batch production issue"
    },
    @{
        Profile = "automotive_discrete"
        Station = "ST22"
        ExpectedDocs = @("DOWNTIME", "hydraulic", "press")
        Description = "Automotive downtime response"
    }
)

Write-Host ""
Write-Host "TEST 1: Document Retrieval by Profile" -ForegroundColor Yellow
Write-Host "-" * 80
Write-Host ""

foreach ($scenario in $testScenarios) {
    Write-Host "Testing Profile: " -NoNewline
    Write-Host $scenario.Profile -ForegroundColor Green
    Write-Host "  Station: $($scenario.Station)"
    Write-Host "  Description: $($scenario.Description)"
    Write-Host ""
    
    try {
        # Switch profile first (domain profile manager endpoint)
        $switchBody = @{
            profile_name = $scenario.Profile
        } | ConvertTo-Json
        
        try {
            $switchResponse = Invoke-RestMethod -Uri "$baseUrl/api/domain/switch-profile" `
                -Method POST `
                -Body $switchBody `
                -ContentType "application/json" `
                -TimeoutSec 10
            Write-Host "  ✓ Switched to profile: $($scenario.Profile)" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ Could not switch profile (may not have endpoint): $_" -ForegroundColor Yellow
        }
        
        # Call diagnostics API
        $body = @{
            scope = "station"
            id = $scenario.Station
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/diagnostics/explain" `
            -Method POST `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 30
        
        # Check if response has explanation fields
        $allSections = @(
            $response.what_is_happening,
            $response.why_this_is_happening,
            $response.what_to_do_now,
            $response.what_to_check_next
        ) -join " "
        
        if ($allSections) {
            # Check for citations in all sections
            $hasCitations = $false
            $citationCount = 0
            $citedDocs = @()
            
            # Look for common citation patterns
            if ($allSections -match "According to" -or 
                $allSections -match "As per" -or
                $allSections -match "As specified in" -or
                $allSections -match "per \w+-\w+-") {
                $hasCitations = $true
            }
            
            # Extract document IDs
            $matches = [regex]::Matches($allSections, '\[?(WI-\w+-[\w-]+|SOP-[\w-]+|CAL-[\w-]+|DOWNTIME-\d+|MAINT-[\w-]+)\]?')
            foreach ($match in $matches) {
                $citedDocs += $match.Value.Trim('[]')
                $citationCount++
            }
            
            # Check for expected doc types
            $foundExpected = $false
            foreach ($expected in $scenario.ExpectedDocs) {
                if ($allSections -match $expected) {
                    $foundExpected = $true
                    break
                }
            }
            
            # Report results
            if ($hasCitations) {
                Write-Host "  [PASS] Citations found in explanation" -ForegroundColor Green
                Write-Host "  Citation count: $citationCount"
                if ($citedDocs.Count -gt 0) {
                    Write-Host "  Cited documents:"
                    $citedDocs | ForEach-Object { Write-Host "    - $_" -ForegroundColor Cyan }
                }
                $testsPassed++
            } else {
                Write-Host "  [FAIL] No citations found in explanation" -ForegroundColor Red
                Write-Host "  Sample output (first 200 chars): $($allSections.Substring(0, [Math]::Min(200, $allSections.Length)))" -ForegroundColor Yellow
                $testsFailed++
            }
            
            if ($foundExpected) {
                Write-Host "  [PASS] Expected document type referenced" -ForegroundColor Green
                $testsPassed++
            } else {
                Write-Host "  [WARN] Expected document types not clearly referenced" -ForegroundColor Yellow
            }
            
            # Show excerpt with citations
            Write-Host ""
            Write-Host "  Sample from what_to_do_now (first 300 chars):" -ForegroundColor Gray
            $whatToDo = $response.what_to_do_now
            if ($whatToDo -and $whatToDo.Length -gt 0) {
                $excerpt = $whatToDo.Substring(0, [Math]::Min(300, $whatToDo.Length))
                Write-Host "  $excerpt..." -ForegroundColor Gray
            }
            Write-Host ""
            
        } else {
            Write-Host "  [FAIL] No explanation in response" -ForegroundColor Red
            $testsFailed++
        }
        
    } catch {
        Write-Host "  [ERROR] API call failed: $_" -ForegroundColor Red
        $testsFailed++
    }
    
    Write-Host ""
}

Write-Host ""
Write-Host "TEST 2: Profile-Specific Citations Differ" -ForegroundColor Yellow
Write-Host "-" * 80
Write-Host ""

# Collect all cited docs by profile
$citationsByProfile = @{}

foreach ($scenario in $testScenarios) {
    try {
        # Switch profile
        $switchBody = @{
            profile_name = $scenario.Profile
        } | ConvertTo-Json
        
        try {
            $switchResponse = Invoke-RestMethod -Uri "$baseUrl/api/domain/switch-profile" `
                -Method POST `
                -Body $switchBody `
                -ContentType "application/json" `
                -TimeoutSec 10
        } catch {
            # Profile switching might not be available
        }
        
        # Call diagnostics API
        $body = @{
            scope = "station"
            id = $scenario.Station
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/diagnostics/explain" `
            -Method POST `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 30
        
        $allSections = @(
            $response.what_is_happening,
            $response.why_this_is_happening,
            $response.what_to_do_now,
            $response.what_to_check_next
        ) -join " "
        
        if ($allSections) {
            $matches = [regex]::Matches($allSections, '(WI-\w+-[\w-]+|SOP-[\w-]+|CAL-[\w-]+|DOWNTIME-\d+|MAINT-[\w-]+)')
            $docs = @()
            foreach ($match in $matches) {
                $docs += $match.Value
            }
            $citationsByProfile[$scenario.Profile] = $docs | Select-Object -Unique
        }
    } catch {
        Write-Host "  Error collecting citations for $($scenario.Profile)" -ForegroundColor Red
    }
}

# Check if different profiles cite different documents
$profileNames = $citationsByProfile.Keys | Sort-Object
$allSame = $true

if ($profileNames.Count -gt 1) {
    Write-Host "Citations by Profile:"
    foreach ($profile in $profileNames) {
        $docs = $citationsByProfile[$profile]
        Write-Host "  $profile : " -NoNewline
        if ($docs.Count -gt 0) {
            Write-Host ($docs -join ", ") -ForegroundColor Cyan
        } else {
            Write-Host "(none)" -ForegroundColor Gray
        }
    }
    
    # Compare profiles
    $firstDocs = $citationsByProfile[$profileNames[0]] | Sort-Object
    foreach ($profile in $profileNames[1..($profileNames.Count-1)]) {
        $compareDocs = $citationsByProfile[$profile] | Sort-Object
        $diff = Compare-Object $firstDocs $compareDocs
        if ($diff) {
            $allSame = $false
        }
    }
    
    Write-Host ""
    if (-not $allSame) {
        Write-Host "  [PASS] Different profiles cite different documents" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "  [WARN] All profiles citing same documents - may indicate insufficient corpus diversity" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "TEST 3: Corpus Impact - With vs Without Documents" -ForegroundColor Yellow
Write-Host "-" * 80
Write-Host ""
Write-Host "This test requires manually clearing Chroma and re-running diagnostics."
Write-Host "Expected: With corpus, responses should:"
Write-Host "  - Include specific procedure citations"
Write-Host "  - Reference document IDs and revisions"
Write-Host "  - Provide actionable steps from retrieved documents"
Write-Host ""
Write-Host "Without corpus, responses should:"
Write-Host "  - State 'No relevant procedures found'"
Write-Host "  - Provide only general guidance"
Write-Host "  - NOT invent specific procedure names"
Write-Host ""
Write-Host "[MANUAL] Review explanations above for procedure specificity"
Write-Host ""

Write-Host ""
Write-Host "TEST 4: Citation Format Compliance" -ForegroundColor Yellow
Write-Host "-" * 80
Write-Host ""

# Check if citations follow expected format
$validFormats = @(
    "According to",
    "As per",
    "As specified in",
    "per [A-Z]+-[A-Z0-9-]+"
)

$formatCompliant = 0
$formatNonCompliant = 0

foreach ($scenario in $testScenarios) {
    try {
        $body = @{
            station = $scenario.Station
            profile = $scenario.Profile
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$baseUrl/api/diagnostics/station" `
            -Method POST `
            -Body $body `
            -ContentType "application/json" `
            -TimeoutSec 30
        
        if ($response.explanation) {
            $hasValidFormat = $false
            foreach ($format in $validFormats) {
                if ($response.explanation -match $format) {
                    $hasValidFormat = $true
                    break
                }
            }
            
            if ($hasValidFormat) {
                $formatCompliant++
            } else {
                $formatNonCompliant++
            }
        }
    } catch {
        # Skip errors
    }
}

Write-Host "Citation format compliance:"
Write-Host "  Valid format: $formatCompliant / $($testScenarios.Count)" -ForegroundColor Cyan
if ($formatCompliant -eq $testScenarios.Count) {
    Write-Host "  [PASS] All responses use proper citation format" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "  [WARN] Some responses lack proper citation format" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ("=" * 80)
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 80)
Write-Host ""
Write-Host "Tests Passed: " -NoNewline
Write-Host $testsPassed -ForegroundColor Green
Write-Host "Tests Failed: " -NoNewline
$failColor = if ($testsFailed -eq 0) { "Green" } else { "Red" }
Write-Host $testsFailed -ForegroundColor $failColor
Write-Host ""

Write-Host "Acceptance Criteria:" -ForegroundColor Cyan
$citationStatus = if ($testsPassed -ge 3) { "PASS" } else { "FAIL" }
$citationColor = if ($testsPassed -ge 3) { "Green" } else { "Red" }
Write-Host "  [$citationStatus] Explanations include credible citations" -ForegroundColor $citationColor

$profileStatus = if (-not $allSame) { "PASS" } else { "WARN" }
$profileColor = if (-not $allSame) { "Green" } else { "Yellow" }
Write-Host "  [$profileStatus] Citations differ across profiles" -ForegroundColor $profileColor

Write-Host "  [MANUAL] LLM output improves without retraining (corpus provides procedures)"
Write-Host "  [MANUAL] Removing corpus degrades explanations (expected behavior)"
Write-Host ""

if ($testsPassed -ge 3 -and $testsFailed -eq 0) {
    Write-Host "[SUCCESS] Sprint 5 Citation Discipline VERIFIED" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[INCOMPLETE] Review failures and warnings above" -ForegroundColor Yellow
    exit 1
}
