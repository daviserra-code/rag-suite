# Comprehensive color fix - replace ALL grey text and white backgrounds
$replacements = @{
    # Grey text colors - ALL variations
    'text-gray-300' = 'text-slate-100'
    'text-gray-400' = 'text-slate-200'
    'text-gray-500' = 'text-slate-200'
    'text-gray-600' = 'text-slate-200'
    'text-gray-700' = 'text-slate-100'
    'text-gray-800' = 'text-white'
    
    # White and light backgrounds - replace with dark
    'bg-white' = 'bg-slate-800'
    'bg-gray-50' = 'bg-slate-800'
    'bg-gray-100' = 'bg-slate-700'
    'bg-blue-50' = 'bg-blue-900'
    'bg-green-50' = 'bg-green-900'
    'bg-orange-50' = 'bg-orange-900'
    'bg-red-50' = 'bg-red-900'
    'bg-yellow-50' = 'bg-yellow-900'
    'bg-purple-50' = 'bg-purple-900'
    
    # Light text on dark backgrounds
    'text-blue-700' = 'text-blue-300'
    'text-blue-600' = 'text-blue-300'
}

# Target all Python screen files
$files = Get-ChildItem -Path "apps\shopfloor_copilot\screens\*.py" -Recurse

$totalReplacements = 0
$filesModified = 0

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw -Encoding UTF8
    $originalContent = $content
    $fileReplacements = 0
    
    foreach ($old in $replacements.Keys) {
        $new = $replacements[$old]
        $matches = ([regex]::Matches($content, [regex]::Escape($old))).Count
        if ($matches -gt 0) {
            $content = $content -replace [regex]::Escape($old), $new
            $fileReplacements += $matches
        }
    }
    
    if ($content -ne $originalContent) {
        Set-Content -Path $file.FullName -Value $content -Encoding UTF8 -NoNewline
        $filesModified++
        $totalReplacements += $fileReplacements
        Write-Host "Fixed $($file.Name) - $fileReplacements replacements" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== COLOR FIX COMPLETE ===" -ForegroundColor Cyan
Write-Host "Files modified: $filesModified" -ForegroundColor Yellow
Write-Host "Total replacements: $totalReplacements" -ForegroundColor Yellow
