param(
    [Parameter(Position = 0)]
    [ValidateSet("help", "setup", "install", "seed", "pipeline", "test", "lint", "qa", "app", "clean")]
    [string]$Task = "help",
    [int]$Matches = 500,
    [int]$Seed = 42,
    [switch]$FailOnDqError
)

$ErrorActionPreference = "Stop"

function Get-PythonExe {
    $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCmd -and $pythonCmd.Source -notlike "*WindowsApps*") {
        return "python"
    }

    $candidates = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "Python3*" } |
        Sort-Object Name -Descending
    foreach ($candidate in $candidates) {
        $realPython = Join-Path $candidate.FullName "python.exe"
        if (Test-Path $realPython) {
            return $realPython
        }
    }

    throw "Python was not found. Install Python 3.11+ and re-run."
}

function Invoke-ProjectCommand {
    param(
        [string[]]$CommandArgs
    )
    $py = Get-PythonExe
    & $py @CommandArgs
}

function Show-Help {
    Write-Host "Usage:"
    Write-Host "  .\run.ps1 setup"
    Write-Host "  .\run.ps1 seed -Matches 280 -Seed 42"
    Write-Host "  .\run.ps1 pipeline [-FailOnDqError]"
    Write-Host "  .\run.ps1 test"
    Write-Host "  .\run.ps1 app"
    Write-Host ""
    Write-Host "Tasks: setup, install, seed, pipeline, test, lint, qa, app, clean"
}

switch ($Task) {
    "help" {
        Show-Help
        break
    }
    "setup" {
        $py = Get-PythonExe
        if (-not (Test-Path ".venv\Scripts\python.exe")) {
            & $py -m venv .venv
        }
        & ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
        & ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"
        break
    }
    "install" {
        Invoke-ProjectCommand -CommandArgs @("-m", "pip", "install", "--upgrade", "pip")
        Invoke-ProjectCommand -CommandArgs @("-m", "pip", "install", "-e", ".[dev]")
        break
    }
    "seed" {
        Invoke-ProjectCommand -CommandArgs @("-m", "src.main", "seed", "--matches", "$Matches", "--seed", "$Seed")
        break
    }
    "pipeline" {
        if ($FailOnDqError) {
            Invoke-ProjectCommand -CommandArgs @("-m", "src.main", "pipeline", "--fail-on-dq-error")
        }
        else {
            Invoke-ProjectCommand -CommandArgs @("-m", "src.main", "pipeline")
        }
        break
    }
    "test" {
        Invoke-ProjectCommand -CommandArgs @("-m", "pytest")
        break
    }
    "lint" {
        Invoke-ProjectCommand -CommandArgs @("-m", "ruff", "check", "src", "tests", "app")
        Invoke-ProjectCommand -CommandArgs @("-m", "black", "--check", "src", "tests", "app")
        break
    }
    "qa" {
        Invoke-ProjectCommand -CommandArgs @("-m", "ruff", "check", "src", "tests", "app")
        Invoke-ProjectCommand -CommandArgs @("-m", "black", "--check", "src", "tests", "app")
        Invoke-ProjectCommand -CommandArgs @("-m", "pytest")
        break
    }
    "app" {
        Invoke-ProjectCommand -CommandArgs @("-m", "streamlit", "run", "app/Home.py")
        break
    }
    "clean" {
        Invoke-ProjectCommand -CommandArgs @("-m", "src.main", "clean")
        break
    }
}
