# Fix light backgrounds in rag-suite subdirectory
$replacements = @{
    # Light background cards -> Dark backgrounds
    "bg-blue-50 border-l-4 border-blue-500" = "bg-blue-900 border-l-4 border-blue-500"
    "bg-green-50 border-l-4 border-green-500" = "bg-green-900 border-l-4 border-green-500"
    "bg-orange-50 border-l-4 border-orange-500" = "bg-orange-900 border-l-4 border-orange-500"
    "bg-red-50 border-l-4 border-red-500" = "bg-red-900 border-l-4 border-red-500"
    "bg-yellow-50 border-l-4 border-yellow-500" = "bg-yellow-900 border-l-4 border-yellow-500"
    
    # Status cards with borders
    "border-red-500 bg-red-50" = "border-red-500 bg-red-900"
    "border-orange-500 bg-orange-50" = "border-orange-500 bg-orange-900"
    "border-yellow-500 bg-yellow-50" = "border-yellow-500 bg-yellow-900"
    "border-green-500 bg-green-50" = "border-green-500 bg-green-900"
    "border-blue-500 bg-blue-50" = "border-blue-500 bg-blue-900"
    "border-gray-500 bg-gray-50" = "border-gray-500 bg-slate-800"
    
    # Light gradient backgrounds -> Dark gradients
    "bg-gradient-to-br from-blue-50 to-indigo-50" = "bg-gradient-to-br from-blue-900 to-indigo-900"
    "bg-gradient-to-br from-green-50 to-emerald-50" = "bg-gradient-to-br from-green-900 to-emerald-900"
    "bg-gradient-to-br from-gray-50 to-gray-100" = "bg-gradient-to-br from-slate-800 to-slate-900"
    
    # Simple light backgrounds
    "bg-blue-50" = "bg-blue-900"
    "bg-green-50" = "bg-green-900"
    "bg-red-50" = "bg-red-900"
    "bg-orange-50" = "bg-orange-900"
    "bg-yellow-50" = "bg-yellow-900"
    "bg-purple-50" = "bg-purple-900"
    "bg-gray-50" = "bg-slate-800"
    
    # Light border colors
    "border-blue-200" = "border-blue-500"
    "border-green-200" = "border-green-500"
    "border-gray-200" = "border-slate-600"
    
    # Hover states with light backgrounds
    "hover:bg-gray-50" = "hover:bg-slate-700"
    "hover:bg-blue-100" = "hover:bg-blue-800"
    "hover:bg-green-100" = "hover:bg-green-800"
    
    # Dark mode conditionals
    "bg-gray-50 dark:bg-gray-800" = "bg-slate-800"
    "bg-blue-50 dark:bg-blue-900" = "bg-blue-900"
    "bg-green-50 dark:bg-green-900/20" = "bg-green-900"
    "bg-blue-50 dark:bg-blue-900/20" = "bg-blue-900"
    "bg-yellow-50 dark:bg-yellow-900/20" = "bg-yellow-900"
    "bg-purple-50 dark:bg-purple-900/20" = "bg-purple-900"
    "hover:bg-gray-50 dark:hover:bg-gray-800" = "hover:bg-slate-700"
    
    # White backgrounds
    "bg-white dark:bg-gray-900" = "bg-slate-800"
}

# Target rag-suite subdirectory
$files = Get-ChildItem -Path "rag-suite\apps\shopfloor_copilot\screens\*.py" -Recurse

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
Write-Host "=== RAG-SUITE SUBDIRECTORY FIX COMPLETE ===" -ForegroundColor Cyan
Write-Host "Files modified: $filesModified" -ForegroundColor Yellow
Write-Host "Total replacements: $totalReplacements" -ForegroundColor Yellow
