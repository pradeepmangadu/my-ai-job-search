# AI Job Search MCP Launcher

Write-Host "Starting AI Job Search MCP..." -ForegroundColor Green

Set-Location $PSScriptRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "ERROR: .venv not found." -ForegroundColor Red
    exit 1
}

Write-Host "Virtual environment activated." -ForegroundColor Cyan
Write-Host "Starting MCP Inspector..." -ForegroundColor Cyan

npx @modelcontextprotocol/inspector python main.py