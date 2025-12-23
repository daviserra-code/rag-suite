# UI Color Enhancement Script - Sprint 4
# This script automatically fixes grey-on-white text issues across all Shopfloor Copilot pages

Write-Host "Starting UI Color Enhancement..." -ForegroundColor Cyan
Write-Host ""

$rootPath = "apps/shopfloor_copilot"
$filesProcessed = 0
$replacementsMade = 0

# Define color replacements (old -> new)
$colorReplacements = @{
    # Grey text replacements
    'text-gray-400' = 'text-slate-300'
    'text-gray-500' = 'text-slate-300'
    'text-gray-600' = 'text-slate-200'
    'text-gray-700' = 'text-slate-100'
    'text-gray-800' = 'text-slate-100'
    'text-gray-900' = 'text-white'
    
    # NiceGUI grey variants
    'text-grey-4' = 'text-slate-300'
    'text-grey-5' = 'text-slate-300'
    'text-grey-6' = 'text-slate-300'
    'text-grey-7' = 'text-slate-200'
    'text-grey-8' = 'text-slate-100'
    'text-grey-9' = 'text-white'
    
    # Background replacements
    'bg-gray-50' = 'bg-slate-800'
    'bg-gray-100' = 'bg-slate-700'
    'bg-gray-200' = 'bg-slate-600'
    'bg-grey-1' = 'bg-slate-800'
    'bg-grey-2' = 'bg-slate-800'
    'bg-grey-3' = 'bg-slate-700'
    
    # Border replacements
    'border-gray-200' = 'border-slate-700'
    'border-gray-300' = 'border-slate-600'
}

function Update-FileColors {
    param([string]$FilePath)
    
    $content = Get-Content $FilePath -Raw
    $originalContent = $content
    $fileChanges = 0
    
    foreach ($old in $colorReplacements.Keys) {
        $new = $colorReplacements[$old]
        $pattern = [regex]::Escape($old)
        
        if ($content -match $pattern) {
            $matches = ([regex]::Matches($content, $pattern)).Count
            $content = $content -replace $pattern, $new
            $fileChanges += $matches
        }
    }
    
    if ($content -ne $originalContent) {
        Set-Content -Path $FilePath -Value $content -NoNewline
        return $fileChanges
    }
    
    return 0
}

Write-Host "Scanning files in: $rootPath" -ForegroundColor Yellow
Write-Host ""

Get-ChildItem -Path $rootPath -Filter "*.py" -Recurse | ForEach-Object {
    $changes = Update-FileColors -FilePath $_.FullName
    
    if ($changes -gt 0) {
        $filesProcessed++
        $replacementsMade += $changes
        $relativePath = $_.FullName -replace [regex]::Escape($PWD.Path + "\"), ""
        Write-Host "  Updated: $relativePath ($changes replacements)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Enhancement Complete!" -ForegroundColor Green
Write-Host "Files updated: $filesProcessed" -ForegroundColor White
Write-Host "Total replacements: $replacementsMade" -ForegroundColor White
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review changes: git diff" -ForegroundColor Gray
Write-Host "  2. Test UI: python apps/shopfloor_copilot/main.py" -ForegroundColor Gray
Write-Host "  3. Read guide: docs/UI_STYLE_GUIDE.md" -ForegroundColor Gray
Write-Host ""
