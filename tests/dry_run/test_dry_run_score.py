"""Tests for the dry-run score / leaderboard command (DRYRUN-SCORE).

This is the MVP read-only scoring command over the JSONL history the
``--append-run-history`` packet produces. The command:

  ``python -m gmc_rebuild.dry_run.score --history PATH [--top N]``

reads the file, validates ``schema_version`` = 1 for every record,
computes a small deterministic score per record from the existing
reconciliation count fields, and prints a compact leaderboard sorted
best-first. Records with ``reconciliation`` = ``null`` are excluded.

Tripwires:

1. **Ranking with mixed outcomes** — a two-record history (one MATCH,
   one MISMATCH) sorts MATCH first with the documented score values.
2. **Null reconciliation exclusion** — records without a recon block
   are excluded from the leaderboard but counted in the footer.
3. **Stable tie ordering** — two records with equal scores appear in
   file insertion order.
4. **--top N truncates and labels the truncation** in the footer.
5. **Missing history file** → exit 1 + ``error: ...`` + no traceback.
6. **Malformed JSON** → exit 1 + ``error: ...`` citing the line number.
7. **Unsupported schema_version** → exit 1 + ``error: ...`` citing the
   bad version.
8. **Missing reconciliation key** → exit 1 + ``error: ...``.
9. **--history is required** (argparse exit 2).
10. **--top must be a positive integer** (argparse exit 2).
11. **End-to-end with the --append-run-history packet** — runs the
    real dry-run twice into a temp JSONL file, then runs the scorer
    over it, asserting the documented leaderboard.

Authorization: ``governance/authorizations/2026-06-20_dryrun-score.md``.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as run_cli
from gmc_rebuild.dry_run.score import (
    RankedRecord,
    ScoreHistoryError,
    format_leaderboard,
    parse_history_text,
    rank_records,
    score_record,
)
from gmc_rebuild.dry_run.score import (
    main as score_cli,
)

_FIXTURES_DIR: Path = Path(__file__).resolve().parent / "fixtures"
_TWO_IDEAS: Path = _FIXTURES_DIR / "signals_two_ideas.json"
_THREE_IDEAS: Path = _FIXTURES_DIR / "signals_three_ideas.json"
_EXPECTED_TWO_MATCH: Path = _FIXTURES_DIR / "expected_positions_match_two_ideas.json"


def _capture_score(argv: list[str]) -> tuple[str, str, int | str | None]:
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code: int | str | None = None
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            score_cli(argv)
    except SystemExit as exc:
        exit_code = exc.code
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


def _capture_run(argv: list[str]) -> None:
    with (
        redirect_stdout(io.StringIO()),
        redirect_stderr(io.StringIO()),
        contextlib.suppress(SystemExit),
    ):
        run_cli(argv)


def _make_record(
    *,
    run_id: str,
    outcome: str = "MATCH",
    matches: int = 0,
    quantity_mismatches: int = 0,
    only_in_simulated: int = 0,
    only_in_expected: int = 0,
    reconciliation: dict[str, object] | None | str = "default",
) -> str:
    """Build a one-line JSONL record string for tests.

    ``reconciliation`` defaults to a populated dict; pass ``None`` for a
    null-reconciliation record, or a custom dict to override fields.
    """
    if reconciliation == "default":
        reconciliation = {
            "outcome": outcome,
            "matches": matches,
            "quantity_mismatches": quantity_mismatches,
            "only_in_simulated": only_in_simulated,
            "only_in_expected": only_in_expected,
            "reconciliation_status": "clean",
        }
    import json as _json

    return _json.dumps(
        {
            "schema_version": 1,
            "run_id": run_id,
            "source": "signals_json",
            "report_date": "2026-06-18",
            "inputs": {
                "signals_file": "ideas.json",
                "db": None,
                "expected_positions_file": None,
                "signal_count": 1,
                "symbols": [],
            },
            "decisions": {
                "total": 0,
                "would_trade": 0,
                "would_skip": 0,
                "by_signal": [],
            },
            "net_positions": [],
            "reconciliation": reconciliation,
        },
        sort_keys=True,
    )


# ---------------------------------------------------------------------------
# 1 & 2. Mixed ranking + null exclusion
# ---------------------------------------------------------------------------


def test_two_records_one_match_one_mismatch_ranks_match_first() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(run_id="exp-a", outcome="MATCH", matches=3)
            + "\n"
            + _make_record(
                run_id="exp-b",
                outcome="MISMATCH",
                matches=1,
                quantity_mismatches=1,
                only_in_simulated=1,
            )
            + "\n",
            encoding="utf-8",
        )
        stdout, stderr, code = _capture_score(["--history", str(history)])
    assert code is None
    assert stderr == ""
    lines = stdout.splitlines()
    assert lines[0].startswith("rank 1. exp-a")
    assert "score=3" in lines[0]
    assert "outcome=MATCH" in lines[0]
    assert lines[1].startswith("rank 2. exp-b")
    assert "score=-1" in lines[1]
    assert "outcome=MISMATCH" in lines[1]
    assert lines[-1] == "ranked 2 records, excluded 0 (no reconciliation)"


def test_null_reconciliation_records_are_excluded_but_counted() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(run_id="exp-a", outcome="MATCH", matches=2)
            + "\n"
            + _make_record(run_id="exp-no-recon", reconciliation=None)
            + "\n"
            + _make_record(run_id="exp-c", outcome="MATCH", matches=1)
            + "\n",
            encoding="utf-8",
        )
        stdout, _, _ = _capture_score(["--history", str(history)])
    lines = stdout.splitlines()
    # exp-no-recon must NOT appear in the leaderboard.
    assert "exp-no-recon" not in stdout
    assert lines[0].startswith("rank 1. exp-a")
    assert lines[1].startswith("rank 2. exp-c")
    assert lines[-1] == "ranked 2 records, excluded 1 (no reconciliation)"


def test_all_null_reconciliation_shows_helpful_empty_leaderboard() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(run_id="exp-x", reconciliation=None)
            + "\n"
            + _make_record(run_id="exp-y", reconciliation=None)
            + "\n",
            encoding="utf-8",
        )
        stdout, _, code = _capture_score(["--history", str(history)])
    assert code is None
    assert "all excluded for null reconciliation" in stdout
    assert "ranked 0 records, excluded 2 (no reconciliation)" in stdout


def test_empty_history_file_shows_empty_leaderboard() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text("", encoding="utf-8")
        stdout, _, code = _capture_score(["--history", str(history)])
    assert code is None
    assert "history file is empty" in stdout
    assert "ranked 0 records, excluded 0" in stdout


def test_blank_lines_in_history_are_skipped() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            "\n"
            + _make_record(run_id="exp-a", outcome="MATCH", matches=1)
            + "\n\n"
            + _make_record(run_id="exp-b", outcome="MATCH", matches=2)
            + "\n\n",
            encoding="utf-8",
        )
        stdout, _, _ = _capture_score(["--history", str(history)])
    # exp-b has higher score so it ranks first.
    lines = stdout.splitlines()
    assert lines[0].startswith("rank 1. exp-b")
    assert lines[1].startswith("rank 2. exp-a")


# ---------------------------------------------------------------------------
# 3. Stable tie ordering
# ---------------------------------------------------------------------------


def test_equal_scores_preserve_file_insertion_order() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(run_id="exp-first", outcome="MATCH", matches=2)
            + "\n"
            + _make_record(run_id="exp-second", outcome="MATCH", matches=2)
            + "\n"
            + _make_record(run_id="exp-third", outcome="MATCH", matches=2)
            + "\n",
            encoding="utf-8",
        )
        stdout, _, _ = _capture_score(["--history", str(history)])
    lines = stdout.splitlines()
    # All three tied at score=2; the file order is the leaderboard order.
    assert lines[0].startswith("rank 1. exp-first")
    assert lines[1].startswith("rank 2. exp-second")
    assert lines[2].startswith("rank 3. exp-third")


# ---------------------------------------------------------------------------
# 4. --top N
# ---------------------------------------------------------------------------


def test_top_n_truncates_and_summary_indicates_truncation() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            "\n".join(_make_record(run_id=f"exp-{i}", outcome="MATCH", matches=i) for i in range(5))
            + "\n",
            encoding="utf-8",
        )
        stdout, _, _ = _capture_score(["--history", str(history), "--top", "2"])
    lines = stdout.splitlines()
    # 5 records (scores 4, 3, 2, 1, 0) — top 2 shows scores 4 and 3.
    assert lines[0].startswith("rank 1. exp-4")
    assert lines[1].startswith("rank 2. exp-3")
    assert "exp-2" not in stdout
    assert lines[-1] == "showing top 2 of 5 ranked records, excluded 0 (no reconciliation)"


def test_top_n_larger_than_record_count_shows_everything() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(run_id="exp-a", outcome="MATCH", matches=1)
            + "\n"
            + _make_record(run_id="exp-b", outcome="MATCH", matches=2)
            + "\n",
            encoding="utf-8",
        )
        stdout, _, _ = _capture_score(["--history", str(history), "--top", "10"])
    # With top >= len, we still show everything; the footer notes that we
    # showed top 2 of 2.
    assert "exp-a" in stdout
    assert "exp-b" in stdout
    assert "ranked 2 records, excluded 0" in stdout


def test_top_zero_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(_make_record(run_id="exp-a") + "\n", encoding="utf-8")
        _, stderr, code = _capture_score(["--history", str(history), "--top", "0"])
    assert code == 2
    assert "must be >= 1" in stderr


def test_top_negative_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(_make_record(run_id="exp-a") + "\n", encoding="utf-8")
        _, _, code = _capture_score(["--history", str(history), "--top", "-1"])
    assert code == 2


def test_top_non_integer_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(_make_record(run_id="exp-a") + "\n", encoding="utf-8")
        _, _, code = _capture_score(["--history", str(history), "--top", "foo"])
    assert code == 2


# ---------------------------------------------------------------------------
# 5 & 6 & 7 & 8. Operator-readable errors
# ---------------------------------------------------------------------------


def test_missing_history_file_is_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        missing = Path(raw_temp) / "nope.jsonl"
        stdout, stderr, code = _capture_score(["--history", str(missing)])
    assert code == 1
    assert stdout == ""
    assert stderr == f"error: history file not found: {missing}\n"
    assert "Traceback" not in stderr


def test_history_path_is_directory_is_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        dir_path = Path(raw_temp) / "is_dir"
        dir_path.mkdir()
        _, stderr, code = _capture_score(["--history", str(dir_path)])
    assert code == 1
    assert "history path is a directory" in stderr
    assert "Traceback" not in stderr


def test_malformed_json_line_cites_line_number() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(run_id="exp-a") + "\n" + "{not json\n",
            encoding="utf-8",
        )
        _, stderr, code = _capture_score(["--history", str(history)])
    assert code == 1
    assert "line 2 is not valid JSON" in stderr
    assert "Traceback" not in stderr


def test_unsupported_schema_version_is_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            '{"schema_version": 99, "run_id": "exp-a", "reconciliation": null}\n',
            encoding="utf-8",
        )
        _, stderr, code = _capture_score(["--history", str(history)])
    assert code == 1
    assert "unsupported schema_version" in stderr
    assert "99" in stderr
    assert "supports 1 only" in stderr


def test_missing_reconciliation_key_is_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            '{"schema_version": 1, "run_id": "exp-a"}\n',
            encoding="utf-8",
        )
        _, stderr, code = _capture_score(["--history", str(history)])
    assert code == 1
    assert "missing 'reconciliation'" in stderr


def test_reconciliation_with_missing_count_field_is_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(
                run_id="exp-a",
                reconciliation={
                    "outcome": "MATCH",
                    "matches": 1,
                    "quantity_mismatches": 0,
                    "only_in_simulated": 0,
                    # only_in_expected intentionally missing
                    "reconciliation_status": "clean",
                },
            )
            + "\n",
            encoding="utf-8",
        )
        _, stderr, code = _capture_score(["--history", str(history)])
    assert code == 1
    assert "only_in_expected" in stderr


def test_negative_reconciliation_count_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(
                run_id="exp-a",
                reconciliation={
                    "outcome": "MATCH",
                    "matches": -5,
                    "quantity_mismatches": 0,
                    "only_in_simulated": 0,
                    "only_in_expected": 0,
                    "reconciliation_status": "clean",
                },
            )
            + "\n",
            encoding="utf-8",
        )
        _, stderr, code = _capture_score(["--history", str(history)])
    assert code == 1
    assert "must be non-negative" in stderr


def test_bool_reconciliation_count_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        history = Path(raw_temp) / "h.jsonl"
        history.write_text(
            _make_record(
                run_id="exp-a",
                reconciliation={
                    "outcome": "MATCH",
                    "matches": True,
                    "quantity_mismatches": 0,
                    "only_in_simulated": 0,
                    "only_in_expected": 0,
                    "reconciliation_status": "clean",
                },
            )
            + "\n",
            encoding="utf-8",
        )
        _, stderr, code = _capture_score(["--history", str(history)])
    assert code == 1
    assert "must be an integer" in stderr


# ---------------------------------------------------------------------------
# 9. --history is required
# ---------------------------------------------------------------------------


def test_history_arg_is_required() -> None:
    _, stderr, code = _capture_score([])
    assert code == 2
    assert "--history" in stderr


# ---------------------------------------------------------------------------
# 10 & 11. End-to-end with the --append-run-history packet
# ---------------------------------------------------------------------------


def test_end_to_end_real_history_then_score() -> None:
    """Drive the real --append-run-history packet twice into a temp
    JSONL file, then run the scorer over it and assert the documented
    leaderboard. This is the MVP learning loop in one test."""
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        history = temp / "history.jsonl"
        # Two-ideas signals against the matching expected → MATCH (score=2).
        _capture_run(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--show-reconciliation",
                "--run-id",
                "exp-match-a",
                "--append-run-history",
                str(history),
            ]
        )
        # Three-ideas signals against the same expected → MISMATCH (score=-1).
        _capture_run(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_THREE_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--show-reconciliation",
                "--run-id",
                "exp-mismatch-b",
                "--append-run-history",
                str(history),
            ]
        )
        stdout, _, code = _capture_score(["--history", str(history)])
    assert code is None
    lines = stdout.splitlines()
    assert lines[0].startswith("rank 1. exp-match-a")
    assert "score=2" in lines[0] and "outcome=MATCH" in lines[0]
    assert lines[1].startswith("rank 2. exp-mismatch-b")
    assert "score=-1" in lines[1] and "outcome=MISMATCH" in lines[1]
    assert "ranked 2 records, excluded 0" in stdout


def test_end_to_end_history_with_no_recon_run_is_excluded() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        temp = Path(raw_temp)
        # Need a temp copy of the DB fixture since --append-run-history is
        # also tested on the insider-cluster source elsewhere.
        history = temp / "history.jsonl"
        _capture_run(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--show-reconciliation",
                "--run-id",
                "exp-with-recon",
                "--append-run-history",
                str(history),
            ]
        )
        # This run carries no --show-reconciliation, so reconciliation = null
        # in its history record and the scorer must exclude it.
        _capture_run(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--run-id",
                "exp-no-recon",
                "--append-run-history",
                str(history),
            ]
        )
        stdout, _, _ = _capture_score(["--history", str(history)])
    assert "exp-with-recon" in stdout
    assert "exp-no-recon" not in stdout
    assert "ranked 1 records, excluded 1 (no reconciliation)" in stdout


# ---------------------------------------------------------------------------
# Pure helper unit tests (no CLI)
# ---------------------------------------------------------------------------


def test_score_record_pure_function() -> None:
    record = {
        "reconciliation": {
            "matches": 5,
            "quantity_mismatches": 2,
            "only_in_simulated": 1,
            "only_in_expected": 0,
        }
    }
    assert score_record(record) == 5 - 2 - 1 - 0


def test_rank_records_returns_ranked_records_and_excluded_count() -> None:
    records = [
        {
            "schema_version": 1,
            "run_id": "low",
            "reconciliation": {
                "outcome": "MISMATCH",
                "matches": 0,
                "quantity_mismatches": 1,
                "only_in_simulated": 0,
                "only_in_expected": 0,
                "reconciliation_status": "clean",
            },
        },
        {
            "schema_version": 1,
            "run_id": "skipped",
            "reconciliation": None,
        },
        {
            "schema_version": 1,
            "run_id": "high",
            "reconciliation": {
                "outcome": "MATCH",
                "matches": 3,
                "quantity_mismatches": 0,
                "only_in_simulated": 0,
                "only_in_expected": 0,
                "reconciliation_status": "clean",
            },
        },
    ]
    ranked, excluded = rank_records(records)
    assert excluded == 1
    assert [r.run_id for r in ranked] == ["high", "low"]
    assert all(isinstance(r, RankedRecord) for r in ranked)
    assert ranked[0].score == 3
    assert ranked[1].score == -1


def test_parse_history_text_raises_on_top_level_list() -> None:
    raised: BaseException | None = None
    try:
        parse_history_text("[]\n")
    except ScoreHistoryError as exc:
        raised = exc
    assert isinstance(raised, ScoreHistoryError)
    assert "line 1" in str(raised)
    assert "JSON object" in str(raised)


def test_format_leaderboard_empty_includes_summary_line() -> None:
    rendered = format_leaderboard([], 0)
    assert "no records to rank" in rendered
    assert "ranked 0 records, excluded 0" in rendered
