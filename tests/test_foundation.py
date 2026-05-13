from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_exists() -> None:
    assert (ROOT / "pyproject.toml").exists()


def test_makefile_exists() -> None:
    assert (ROOT / "Makefile").exists()


def test_windows_make_wrapper_exists() -> None:
    assert (ROOT / "make.ps1").exists()


def test_ci_workflow_exists() -> None:
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists()


def test_package_exists() -> None:
    assert (ROOT / "marketimmune" / "__init__.py").exists()


def test_docs_exist() -> None:
    assert (ROOT / "docs" / "threat_model.md").exists()
    assert (ROOT / "docs" / "benchmark_spec.md").exists()
    assert (ROOT / "docs" / "limitations.md").exists()


def test_configs_exist() -> None:
    assert (ROOT / "configs" / "scenarios" / "taxonomy.yaml").exists()
    assert (ROOT / "configs" / "benchmark" / "tasks.yaml").exists()
