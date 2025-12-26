# Screenshot Verification Script
# Shopfloor Copilot Documentation - December 2025

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Screenshot Verification Tool" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$screenshotDir = "C:\Users\Davide\VS-Code Solutions\rag-suite\docs\shopfloor-copilot\screenshots"

# Required screenshots with descriptions
$requiredScreenshots = @(
    @{Name="manual_01_landing_overview.png"; Description="Landing Page Overview"},
    @{Name="manual_02_opc_studio_overview.png"; Description="OPC Studio Entry Point"},
    @{Name="manual_03_profile_selector.png"; Description="Profile Selector"},
    @{Name="manual_05_semantic_snapshot.png"; Description="Semantic Runtime Snapshot"},
    @{Name="manual_06_material_context_present.png"; Description="Material Context Present"},
    @{Name="manual_07_missing_material_evidence_ad.png"; Description="Missing Material Evidence (A&D) [CRITICAL]"},
    @{Name="manual_08_diagnostics_blocking_ad.png"; Description="Diagnostics with Blocking (A&D)"},
    @{Name="manual_09_violations_list.png"; Description="Violations List"},
    @{Name="manual_10_violation_timeline.png"; Description="Violation Timeline"},
    @{Name="manual_11_rag_citations.png"; Description="Explanation with Citations"},
    @{Name="manual_13_opc_browsing.png"; Description="OPC Browsing"},
    @{Name="manual_14_custom_tags.png"; Description="Custom Tags"},
    @{Name="manual_15_simulation.png"; Description="Simulation"},
    @{Name="manual_16_demo_ad_blocking.png"; Description="Demo A&D Blocking"},
    @{Name="manual_17_demo_pharma_blocking.png"; Description="Demo Pharma Blocking"},
    @{Name="manual_18_demo_happy_path.png"; Description="Demo Happy Path"}
)

# Check if directory exists
if (-not (Test-Path $screenshotDir)) {
    Write-Host "❌ Screenshots directory not found: $screenshotDir" -ForegroundColor Red
    Write-Host "Creating directory..." -ForegroundColor Yellow
    New-Item -Path $screenshotDir -ItemType Directory | Out-Null
    Write-Host "✅ Directory created." -ForegroundColor Green
}

# Check each required screenshot
$foundCount = 0
$missingCount = 0
$missingFiles = @()

Write-Host "Checking for required screenshots...`n" -ForegroundColor Yellow

foreach ($screenshot in $requiredScreenshots) {
    $filePath = Join-Path $screenshotDir $screenshot.Name
    if (Test-Path $filePath) {
        $fileInfo = Get-Item $filePath
        $fileSizeKB = [math]::Round($fileInfo.Length / 1KB, 2)
        
        # Check file size (warn if too small or too large)
        $sizeStatus = "✅"
        $sizeColor = "Green"
        if ($fileSizeKB -lt 20) {
            $sizeStatus = "⚠️"
            $sizeColor = "Yellow"
            $warning = " (too small?)"
        } elseif ($fileSizeKB -gt 5000) {
            $sizeStatus = "⚠️"
            $sizeColor = "Yellow"
            $warning = " (very large, consider compression)"
        } else {
            $warning = ""
        }
        
        Write-Host "$sizeStatus " -NoNewline -ForegroundColor $sizeColor
        Write-Host "$($screenshot.Name) " -NoNewline -ForegroundColor White
        Write-Host "($fileSizeKB KB)$warning" -ForegroundColor Gray
        Write-Host "   └─ $($screenshot.Description)" -ForegroundColor DarkGray
        $foundCount++
    } else {
        Write-Host "❌ " -NoNewline -ForegroundColor Red
        Write-Host "$($screenshot.Name) " -NoNewline -ForegroundColor White
        Write-Host "MISSING" -ForegroundColor Red
        Write-Host "   └─ $($screenshot.Description)" -ForegroundColor DarkGray
        $missingCount++
        $missingFiles += $screenshot.Name
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Required: " -NoNewline
Write-Host $requiredScreenshots.Count -ForegroundColor White
Write-Host "Found:          " -NoNewline
Write-Host $foundCount -ForegroundColor Green
Write-Host "Missing:        " -NoNewline
if ($missingCount -gt 0) {
    Write-Host $missingCount -ForegroundColor Red
} else {
    Write-Host $missingCount -ForegroundColor Green
}

# Completion percentage
$completionPct = [math]::Round(($foundCount / $requiredScreenshots.Count) * 100, 2)
Write-Host "`nCompletion:     " -NoNewline
if ($completionPct -eq 100) {
    Write-Host "$completionPct% 🎉" -ForegroundColor Green
} elseif ($completionPct -ge 50) {
    Write-Host "$completionPct%" -ForegroundColor Yellow
} else {
    Write-Host "$completionPct%" -ForegroundColor Red
}

# Missing files detail
if ($missingCount -gt 0) {
    Write-Host "`n⚠️  Missing Files:" -ForegroundColor Yellow
    foreach ($file in $missingFiles) {
        Write-Host "   - $file" -ForegroundColor Gray
    }
    Write-Host "`nRefer to CAPTURE_CHECKLIST.md for capture instructions." -ForegroundColor Cyan
}

# Quality checks
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Quality Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($foundCount -gt 0) {
    Write-Host "Run these manual checks for each screenshot:" -ForegroundColor Yellow
    Write-Host "  1. Resolution 1920x1080 or similar (not tiny)" -ForegroundColor Gray
    Write-Host "  2. Dark theme consistent" -ForegroundColor Gray
    Write-Host "  3. Text readable (no blur)" -ForegroundColor Gray
    Write-Host "  4. Content matches specification" -ForegroundColor Gray
    Write-Host "  5. No personal/sensitive data visible" -ForegroundColor Gray
    Write-Host "  6. No browser UI clutter (tabs, bookmarks)" -ForegroundColor Gray
}

# Exit status
Write-Host "`n========================================`n" -ForegroundColor Cyan
if ($completionPct -eq 100) {
    Write-Host "✅ All screenshots captured! Ready for STEP C (manual assembly)." -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Capture incomplete. Continue capturing remaining screenshots." -ForegroundColor Yellow
    exit 1
}
