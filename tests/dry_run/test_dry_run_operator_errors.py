"""Tests for operator-readable insider-cluster DB error handling (DRYRUN-OPERATOR-ERRORS).

The ``python -m gmc_rebuild.dry_run --source insider_cluster --db PATH``
operator path has three expected operator-data failures that an operator
will routinely hit (typo'd path, wrong working directory, fresh DB without
the expected schema, empty DB without rows yet). All three previously
surfaced as 20+-line Python tracebacks. This suite locks in the single-line
``error: ...`` diagnostic plus non-zero exit + no stdout for each.

Tripwires:

1. **Missing DB** ⇒ exit 1, stderr ``"error: insider-cluster DB not
   found: <path>"``, no traceback, no stdout.
2. **Corrupt / wrong-schema DB** (file exists but has no
   ``backtest_results`` table) ⇒ exit 1, stderr
   ``"error: insider-cluster DB is not a valid backtest_results database:
   <path>"``, no traceback, no stdout.
3. **Empty ``backtest_results`` table** (schema present, no rows) ⇒
   exit 1, stderr ``"error: insider-cluster DB has no rows in
   backtest_results: <path>"``, no traceback, no stdout.
4. **Happy path unchanged**: with the committed NKE fixture the existing
   no-flag stdout is byte-for-byte identical to the locked literal.
5. **Argparse usage errors keep exit 2** so the existing ``error: ...``
   diagnostic exit code is distinguishable from a usage error.

Mirrors the no-``pytest.raises`` convention used by the sibling
``test_dry_run_emit_json.py`` /
``test_dry_run_emit_reconciliation_json.py`` /
``test_dry_run_show_reconciliation.py`` suites.

Authorization: ``governance/authorizations/2026-06-20_dryrun-operator-errors.md``.
"""

from __future__ import annotations

import io
import shutil
import sqlite3
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as cli_main

_FIXTURE: Path = (
    Path(__file__).resolve().parents[1] / "insider_cluster_intake" / "fixtures" / "sample.db"
)


_EXPECTED_NO_FLAG_STDOUT: str = (
    "daily_report: 2026-06-18\n"
    "decisions: 1 total, 1 would_trade, 0 would_skip\n"
    "reconciliation: clean\n"
    "net_positions:\n"
    "  - NKE: 163\n"
    "applied_intent_ids:\n"
    "  - simoi-34836e27172d51b4d97d5f99a0f8cdca2ef84d855c18ab14e86dafe3db288e11\n"
    "\n"
    "safety_verdict: clear=True, blockers=none\n"
    "decision: WOULD_TRADE insider-NKE-2025-12-29 reasons=none\n"
)


def _run_cli(argv: list[str]) -> tuple[str, str, int | str | None]:
    """Invoke ``cli_main`` capturing stdout, stderr, and exit code.

    Returns ``(stdout, stderr, exit_code)``. ``exit_code`` is ``None`` if
    the CLI returned normally, otherwise the int / str carried on
    :class:`SystemExit`.
    """
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code: int | str | None = None
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            cli_main(argv)
    except SystemExit as exc:
        exit_code = exc.code
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


# ---------------------------------------------------------------------------
# 1. Missing --db file ⇒ exit 1, single-line diagnostic, no traceback
# ---------------------------------------------------------------------------


def test_missing_db_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        missing = Path(raw_temp) / "nonexistent.db"
        stdout, stderr, exit_code = _run_cli(["--source", "insider_cluster", "--db", str(missing)])
    assert exit_code == 1
    assert stdout == ""
    assert stderr == f"error: insider-cluster DB not found: {missing}\n"
    # No Python traceback prefix in any form.
    assert "Traceback" not in stderr
    assert "FileNotFoundError" not in stderr


# ---------------------------------------------------------------------------
# 2. Corrupt / wrong-schema DB ⇒ exit 1, single-line diagnostic, no traceback
# ---------------------------------------------------------------------------


def test_wrong_schema_db_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "wrong_schema.db"
        # Real SQLite file but no `backtest_results` table.
        conn = sqlite3.connect(bad)
        try:
            conn.execute("CREATE TABLE something_else (id INTEGER PRIMARY KEY)")
            conn.commit()
        finally:
            conn.close()
        stdout, stderr, exit_code = _run_cli(["--source", "insider_cluster", "--db", str(bad)])
    assert exit_code == 1
    assert stdout == ""
    assert stderr == (
        f"error: insider-cluster DB is not a valid backtest_results database: {bad}\n"
    )
    assert "Traceback" not in stderr
    assert "OperationalError" not in stderr
    assert "sqlite3" not in stderr


def test_non_sqlite_file_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        garbage = Path(raw_temp) / "garbage.db"
        garbage.write_bytes(b"this is not a sqlite database")
        stdout, stderr, exit_code = _run_cli(["--source", "insider_cluster", "--db", str(garbage)])
    assert exit_code == 1
    assert stdout == ""
    assert stderr == (
        f"error: insider-cluster DB is not a valid backtest_results database: {garbage}\n"
    )
    assert "Traceback" not in stderr


# ---------------------------------------------------------------------------
# 3. Empty backtest_results table ⇒ exit 1, single-line diagnostic
# ---------------------------------------------------------------------------


def test_empty_backtest_results_table_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        empty = Path(raw_temp) / "empty.db"
        conn = sqlite3.connect(empty)
        try:
            conn.execute(
                "CREATE TABLE backtest_results ("
                "ticker TEXT, entry_price REAL, num_insiders INT, "
                "total_dollars REAL, roles TEXT, has_ceo INT, has_cfo INT, "
                "signal_date TEXT, entry_date TEXT)"
            )
            conn.commit()
        finally:
            conn.close()
        stdout, stderr, exit_code = _run_cli(["--source", "insider_cluster", "--db", str(empty)])
    assert exit_code == 1
    assert stdout == ""
    assert stderr == (f"error: insider-cluster DB has no rows in backtest_results: {empty}\n")
    assert "Traceback" not in stderr
    assert "LookupError" not in stderr


# ---------------------------------------------------------------------------
# 4. Happy path is byte-for-byte unchanged
# ---------------------------------------------------------------------------


def test_happy_path_stdout_unchanged_with_error_handler_in_place() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        db_copy = Path(raw_temp) / "sample.db"
        shutil.copy(_FIXTURE, db_copy)
        stdout, stderr, exit_code = _run_cli(["--source", "insider_cluster", "--db", str(db_copy)])
    assert exit_code is None
    assert stderr == ""
    assert stdout == _EXPECTED_NO_FLAG_STDOUT


# ---------------------------------------------------------------------------
# 5. Argparse usage errors keep exit 2 (distinct from operator-data exit 1)
# ---------------------------------------------------------------------------


def test_argparse_usage_error_still_exits_two() -> None:
    # --emit-json on the synthetic source is a usage error, not an
    # operator-data error; argparse exits with code 2.
    _, stderr, exit_code = _run_cli(["--source", "synthetic", "--emit-json", "-"])
    assert exit_code == 2
    assert "insider_cluster" in stderr
