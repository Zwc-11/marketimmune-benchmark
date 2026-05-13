param(
    [Parameter(Position = 0)]
    [ValidateSet("install", "lint", "typecheck", "test", "coverage", "phase-metrics", "phase46", "phase79", "ci")]
    [string]$Target = "ci"
)

$ErrorActionPreference = "Stop"
$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

function Assert-LastExitCode {
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

switch ($Target) {
    "install" { & $Python -m pip install -e ".[dev]"; Assert-LastExitCode }
    "lint" { & $Python -m ruff check .; Assert-LastExitCode }
    "typecheck" { & $Python scripts/typecheck.py; Assert-LastExitCode }
    "test" { & $Python -m pytest; Assert-LastExitCode }
    "coverage" {
        & $Python -m coverage run -m pytest; Assert-LastExitCode
        & $Python -m coverage report; Assert-LastExitCode
    }
    "phase-metrics" { & $Python scripts/phase_metrics.py; Assert-LastExitCode }
    "phase46" {
        & $Python scripts/run_replay.py; Assert-LastExitCode
        & $Python scripts/generate_scenarios.py; Assert-LastExitCode
        & $Python scripts/run_rule_baseline.py; Assert-LastExitCode
        & $Python scripts/phase46_metrics.py; Assert-LastExitCode
    }
    "phase79" {
        & $Python scripts/generate_scenarios.py --count 600 --events-per-scenario 30 --clean; Assert-LastExitCode
        & $Python scripts/run_benchmark.py; Assert-LastExitCode
        & $Python scripts/train_order_mtpp.py; Assert-LastExitCode
        & $Python scripts/train_order_s2p2.py; Assert-LastExitCode
        & $Python scripts/phase79_metrics.py; Assert-LastExitCode
    }
    "ci" {
        & $Python -m ruff check .; Assert-LastExitCode
        & $Python scripts/typecheck.py; Assert-LastExitCode
        & $Python -m pytest; Assert-LastExitCode
        & $Python -m coverage run -m pytest; Assert-LastExitCode
        & $Python -m coverage report; Assert-LastExitCode
        & $Python scripts/phase_metrics.py; Assert-LastExitCode
    }
}
