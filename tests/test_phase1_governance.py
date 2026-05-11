"""Phase 1 governance placeholder tests."""

from pathlib import Path


def test_phase1_has_governance_artifacts() -> None:
    """Keep pytest meaningful before Phase 2 production modules exist."""
    root = Path(__file__).resolve().parents[1]

    required_paths = [
        root / "README.md",
        root / "MASTER_STATUS.md",
        root / "AI_WORKFLOW.md",
        root / ".pre-commit-config.yaml",
        root / "pyproject.toml",
        root / "docs" / "decisions" / "ADR-template.md",
        root / "docs" / "decisions" / "ADR-008_monitoring_cadence_and_ai_monitor_role.md",
        root / "docs" / "deploys" / "deploy-log-template.md",
        root / "monitoring" / "daily" / "daily-report-template.md",
        root / "reviews" / "review-request-template.md",
        root / "governance" / "authorizations" / "2026-05-11_p2-01.md",
    ]

    for path in required_paths:
        assert path.is_file(), f"required governance artifact missing: {path}"
        assert path.stat().st_size > 0, f"required governance artifact empty: {path}"


def test_adr_008_records_mode_a_and_mode_b() -> None:
    """ADR-008 is the only durable record of the Backup-AI Mode A / Mode B split.

    A future PR that silently replaces its body must still fail this test, not just
    the existence check. The content markers below are the load-bearing terms the
    rest of the governance docs cite (AI_WORKFLOW.md §1.4 and §4, MASTER_STATUS.md §1).
    """
    root = Path(__file__).resolve().parents[1]
    adr = root / "docs" / "decisions" / "ADR-008_monitoring_cadence_and_ai_monitor_role.md"
    text = adr.read_text(encoding="utf-8")

    required_markers = [
        "Mode A",
        "Mode B",
        "Gate Reviewer",
        "Continuous Governance Monitor",
        "active workday",
        "monitoring/daily",
    ]
    for marker in required_markers:
        assert marker in text, (
            f"ADR-008 missing required marker {marker!r}; "
            f"AI_WORKFLOW.md §1.4 and MASTER_STATUS.md §1 depend on this term."
        )
