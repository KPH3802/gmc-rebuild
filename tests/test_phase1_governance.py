"""Phase 1 governance placeholder tests."""

from pathlib import Path


def test_phase1_has_governance_artifacts() -> None:
    """Keep pytest meaningful before Phase 2 production modules exist."""
    root = Path(__file__).resolve().parents[1]

    required_paths = [
        root / "README.md",
        root / ".pre-commit-config.yaml",
        root / "pyproject.toml",
        root / "docs" / "decisions" / "ADR-template.md",
        root / "docs" / "deploys" / "deploy-log-template.md",
        root / "monitoring" / "daily" / "daily-report-template.md",
        root / "reviews" / "review-request-template.md",
    ]

    assert all(path.is_file() and path.stat().st_size > 0 for path in required_paths)
