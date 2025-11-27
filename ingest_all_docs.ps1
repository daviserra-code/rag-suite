"""
PowerShell script to ingest documents via HTTP API
Run this from the host machine: powershell ./ingest_all_docs.ps1
"""

$API_URL = "http://localhost:8000/ingest"
$DOCS_PATH = "data/documents"
$APP_NAME = "shopfloor_docs"

$ingestedCount = 0
$errorCount = 0

Write-Host "Starting document ingestion..." -ForegroundColor Green
Write-Host ""

# SOPs folder
Write-Host "Ingesting SOPs..." -ForegroundColor Cyan
Get-ChildItem "$DOCS_PATH/SOPs" -Filter *.md | ForEach-Object {
    try {
        $filePath = $_.FullName
        Write-Host "  Uploading: $($_.Name)"
        
        $form = @{
            app = $APP_NAME
            doctype = "procedure"
            file = Get-Item $filePath
        }
        
        $response = Invoke-RestMethod -Uri $API_URL -Method Post -Form $form
        Write-Host "    Success" -ForegroundColor Green
        $ingestedCount++
    }
    catch {
        Write-Host "    Error: $_" -ForegroundColor Red
        $errorCount++
    }
}

# Safety folder
Write-Host "`nIngesting Safety documents..." -ForegroundColor Cyan
Get-ChildItem "$DOCS_PATH/safety" -Include *.md,*.txt -Recurse | ForEach-Object {
    try {
        $filePath = $_.FullName
        Write-Host "  Uploading: $($_.Name)"
        
        $form = @{
            app = $APP_NAME
            doctype = "safety"
            file = Get-Item $filePath
        }
        
        $response = Invoke-RestMethod -Uri $API_URL -Method Post -Form $form
        Write-Host "    Success" -ForegroundColor Green
        $ingestedCount++
    }
    catch {
        Write-Host "    Error: $_" -ForegroundColor Red
        $errorCount++
    }
}

# Quality folder
Write-Host "`nIngesting Quality documents..." -ForegroundColor Cyan
Get-ChildItem "$DOCS_PATH/quality" -Filter *.md | ForEach-Object {
    try {
        $filePath = $_.FullName
        Write-Host "  Uploading: $($_.Name)"
        
        $form = @{
            app = $APP_NAME
            doctype = "quality"
            file = Get-Item $filePath
        }
        
        $response = Invoke-RestMethod -Uri $API_URL -Method Post -Form $form
        Write-Host "    Success" -ForegroundColor Green
        $ingestedCount++
    }
    catch {
        Write-Host "    Error: $_" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host "`n========================================" -ForegroundColor Yellow
Write-Host "Ingestion Summary:" -ForegroundColor Yellow
Write-Host "  Successfully ingested: $ingestedCount documents" -ForegroundColor Green
Write-Host "  Errors: $errorCount documents" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Yellow
