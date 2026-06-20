"""Tests for the dry-run ``--source signals_json --signals-file`` input
(DRYRUN-SIGNALS-JSON).

This is the MVP learning-loop input: the operator describes a batch of
trading-idea signals in a small local JSON file, and the dry-run loop
threads every signal through the same merged P6-01..P6-06 pipeline that
the synthetic and insider-cluster paths use. The cycle exposes the
multi-decision summary, the simulated portfolio, the decision JSON
payload, and the reconciliation surfaces — so the operator can compare
outcomes across experiments by changing the input file and re-running.

Tripwires:

1. **Multi-signal stdout summary** — the documented "decisions:" block
   lists every signal in caller-supplied order with its outcome.
2. **Portfolio aggregation** — sequential application of each
   WOULD_TRADE order intent produces a deterministic multi-symbol
   simulated portfolio.
3. **--emit-json over signals_json** — the decision JSON payload carries
   one record per signal, with symbol / side / quantity / outcome /
   rationale / verdict_clear, in caller-supplied order. The summary
   counts agree with the DailyReport.
4. **--show-reconciliation over signals_json (self-comparison)** — the
   reconciliation text block lists every simulated position as a match
   and produces ``outcome=MATCH`` by construction.
5. **--expected-positions over signals_json (MATCH and MISMATCH)** —
   an independent expected-positions fixture equal to the simulated
   portfolio yields MATCH; a different one yields MISMATCH with the
   documented quantity_mismatches / only_in_expected entries.
6. **Cross-experiment comparison** — running the SAME ``--expected-
   positions`` against TWO different signals files produces different
   reconciliation outcomes: a "we built the expected portfolio" run vs
   a "we built a different one" run. This is the learning loop.
7. **Operator-readable errors** — missing file, malformed JSON, missing
   required keys, bad side value, non-integer quantity, duplicate
   intent_id, invalid signal-intent invariants each surface as
   ``error: ...`` + exit 1 + empty stdout + no traceback.
8. **CLI usage errors** — ``--signals-file`` without ``--source=signals_json``
   is rejected with exit 2; ``--source signals_json`` without
   ``--signals-file`` is rejected with exit 2.
9. **Default no-flag synthetic stdout unchanged** — adding the new
   source choice does not change the default synthetic output.

Authorization: ``governance/authorizations/2026-06-20_dryrun-signals-json.md``.
"""

from __future__ import annotations

import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from gmc_rebuild.dry_run.__main__ import main as cli_main
from gmc_rebuild.dry_run._signals_file import SignalsFileSchemaError, load_signals
from gmc_rebuild.signal_intake import SignalSide

_FIXTURES_DIR: Path = Path(__file__).resolve().parent / "fixtures"
_TWO_IDEAS: Path = _FIXTURES_DIR / "signals_two_ideas.json"
_THREE_IDEAS: Path = _FIXTURES_DIR / "signals_three_ideas.json"
_EXPECTED_TWO_MATCH: Path = _FIXTURES_DIR / "expected_positions_match_two_ideas.json"


# The deterministic stdout summary for the two-ideas fixture.
_EXPECTED_TWO_IDEAS_STDOUT: str = (
    "daily_report: 2026-06-18\n"
    "decisions: 2 total, 2 would_trade, 0 would_skip\n"
    "reconciliation: clean\n"
    "net_positions:\n"
    "  - AAPL: 10\n"
    "  - TSLA: -5\n"
    "applied_intent_ids:\n"
    "  - simoi-3abecd6afd2c8008fd2bc17fd40b1ce5bf618a0d78f3ae6321715b58bce554ff\n"
    "  - simoi-f01acd4b83552e04564f490c80d6ab2ab0bdf878a9f21debb37a25ab09926ed2\n"
    "\n"
    "safety_verdict: clear=True, blockers=none\n"
    "decisions:\n"
    "  - WOULD_TRADE exp-1-aapl-long reasons=none\n"
    "  - WOULD_TRADE exp-2-tsla-short reasons=none\n"
)


def _run_cli(argv: list[str]) -> tuple[str, str, int | str | None]:
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
# 1 & 2. Multi-signal stdout summary and portfolio aggregation
# ---------------------------------------------------------------------------


def test_signals_json_two_ideas_renders_documented_multi_decision_summary() -> None:
    stdout, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(_TWO_IDEAS)])
    assert code is None
    assert stderr == ""
    assert stdout == _EXPECTED_TWO_IDEAS_STDOUT


def test_signals_json_three_ideas_aggregates_three_positions() -> None:
    stdout, _, _ = _run_cli(["--source", "signals_json", "--signals-file", str(_THREE_IDEAS)])
    # decisions header
    assert "decisions: 3 total, 3 would_trade, 0 would_skip" in stdout
    # all three symbols present in net_positions (canonical order is sorted)
    assert "  - AAPL: 7" in stdout
    assert "  - MSFT: 3" in stdout
    assert "  - TSLA: -5" in stdout
    # decisions block lists every intent_id in caller-supplied order
    decisions_idx = stdout.index("decisions:\n  -")
    decisions_block = stdout[decisions_idx:]
    aapl_idx = decisions_block.index("exp-A-aapl-long")
    msft_idx = decisions_block.index("exp-B-msft-long")
    tsla_idx = decisions_block.index("exp-C-tsla-short")
    assert aapl_idx < msft_idx < tsla_idx


# ---------------------------------------------------------------------------
# 3. --emit-json over signals_json carries the per-signal payload
# ---------------------------------------------------------------------------


def test_emit_json_over_signals_json_emits_per_signal_records() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        out = Path(raw_temp) / "ideas_run.json"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--emit-json",
                str(out),
            ]
        )
        payload = json.loads(out.read_text())
    assert payload["as_of"] == "2026-06-18"
    assert payload["summary"] == {"total": 2, "would_trade": 2, "would_skip": 0}
    assert payload["decisions"] == [
        {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 10,
            "outcome": "WOULD_TRADE",
            "rationale": "experimental: AAPL earnings beat hypothesis",
            "verdict_clear": True,
        },
        {
            "symbol": "TSLA",
            "side": "SELL",
            "quantity": 5,
            "outcome": "WOULD_TRADE",
            "rationale": "experimental: TSLA delivery miss hypothesis",
            "verdict_clear": True,
        },
    ]


# ---------------------------------------------------------------------------
# 4. --show-reconciliation self-comparison MATCH
# ---------------------------------------------------------------------------


def test_show_reconciliation_self_compare_over_signals_json_is_match() -> None:
    stdout, _, _ = _run_cli(
        [
            "--source",
            "signals_json",
            "--signals-file",
            str(_TWO_IDEAS),
            "--show-reconciliation",
        ]
    )
    assert "dry_run_reconciliation:" in stdout
    assert "outcome: MATCH" in stdout
    # Both simulated positions appear in the matches block.
    assert "    - AAPL: 10" in stdout
    assert "    - TSLA: -5" in stdout
    # Summary counts.
    assert (
        "summary: 2 matches, 0 quantity_mismatches, 0 only_in_simulated, 0 only_in_expected"
    ) in stdout


# ---------------------------------------------------------------------------
# 5. --expected-positions MATCH and MISMATCH over signals_json
# ---------------------------------------------------------------------------


def test_expected_positions_match_over_signals_json_is_match() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        out = Path(raw_temp) / "recon.json"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--emit-reconciliation-json",
                str(out),
            ]
        )
        payload = json.loads(out.read_text())
    assert payload["outcome"] == "MATCH"
    assert payload["matches"] == [
        {"symbol": "AAPL", "quantity": 10},
        {"symbol": "TSLA", "quantity": -5},
    ]
    assert payload["quantity_mismatches"] == []


def test_expected_positions_mismatch_over_signals_json_is_mismatch() -> None:
    # Three-ideas fixture: simulated portfolio is AAPL:7, MSFT:3, TSLA:-5
    # but the expected-positions fixture says AAPL:10, TSLA:-5 (no MSFT).
    # MISMATCH on AAPL quantity, only_in_simulated for MSFT.
    with tempfile.TemporaryDirectory() as raw_temp:
        out = Path(raw_temp) / "recon.json"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_THREE_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--emit-reconciliation-json",
                str(out),
            ]
        )
        payload = json.loads(out.read_text())
    assert payload["outcome"] == "MISMATCH"
    assert payload["quantity_mismatches"] == [
        {"symbol": "AAPL", "simulated_quantity": 7, "expected_quantity": 10}
    ]
    assert payload["only_in_simulated"] == [{"symbol": "MSFT", "quantity": 3}]
    assert payload["matches"] == [{"symbol": "TSLA", "quantity": -5}]


# ---------------------------------------------------------------------------
# 6. Cross-experiment comparison — the learning loop in action
# ---------------------------------------------------------------------------


def test_two_experiments_against_same_expected_yield_different_outcomes() -> None:
    """The MVP learning loop: same expected-positions, two different
    signals files, two different reconciliation outcomes — proving the
    operator can iterate on trading ideas and observe the delta."""
    with tempfile.TemporaryDirectory() as raw_temp:
        run_a = Path(raw_temp) / "run_a.json"
        run_b = Path(raw_temp) / "run_b.json"
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_TWO_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--emit-reconciliation-json",
                str(run_a),
            ]
        )
        _run_cli(
            [
                "--source",
                "signals_json",
                "--signals-file",
                str(_THREE_IDEAS),
                "--expected-positions",
                str(_EXPECTED_TWO_MATCH),
                "--emit-reconciliation-json",
                str(run_b),
            ]
        )
        payload_a = json.loads(run_a.read_text())
        payload_b = json.loads(run_b.read_text())
    assert payload_a["outcome"] == "MATCH"
    assert payload_b["outcome"] == "MISMATCH"
    # The difference is visible structurally, not just in the outcome —
    # which is the whole point of recording the runs for comparison.
    assert payload_a["matches"] != payload_b["matches"]
    assert payload_a["quantity_mismatches"] != payload_b["quantity_mismatches"]


# ---------------------------------------------------------------------------
# 7. Operator-readable errors
# ---------------------------------------------------------------------------


def test_missing_signals_file_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        missing = Path(raw_temp) / "nope.json"
        stdout, stderr, code = _run_cli(
            ["--source", "signals_json", "--signals-file", str(missing)]
        )
    assert code == 1
    assert stdout == ""
    assert stderr == f"error: signals file not found: {missing}\n"
    assert "Traceback" not in stderr


def test_malformed_signals_json_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "bad.json"
        bad.write_text("{ not json", encoding="utf-8")
        stdout, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(bad)])
    assert code == 1
    assert stdout == ""
    assert stderr.startswith(f"error: invalid signals file {bad}: ")
    assert "not valid JSON" in stderr
    assert "Traceback" not in stderr


def test_missing_signals_key_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "no_key.json"
        bad.write_text('{"other": []}', encoding="utf-8")
        _, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(bad)])
    assert code == 1
    assert "missing required 'signals' key" in stderr


def test_invalid_side_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "bad_side.json"
        bad.write_text(
            '{"signals": [{"intent_id": "x", "symbol": "AAPL", "side": "MAYBE", '
            '"quantity": 1, "rationale": "hello"}]}',
            encoding="utf-8",
        )
        _, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(bad)])
    assert code == 1
    assert "BUY" in stderr and "SELL" in stderr


def test_non_integer_quantity_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "bad_qty.json"
        bad.write_text(
            '{"signals": [{"intent_id": "x", "symbol": "AAPL", "side": "BUY", '
            '"quantity": 1.5, "rationale": "hello"}]}',
            encoding="utf-8",
        )
        _, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(bad)])
    assert code == 1
    assert "positive integer" in stderr


def test_duplicate_intent_id_produces_operator_readable_error() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "dup.json"
        bad.write_text(
            '{"signals": ['
            '{"intent_id": "x", "symbol": "AAPL", "side": "BUY", '
            '"quantity": 1, "rationale": "hello"},'
            '{"intent_id": "x", "symbol": "MSFT", "side": "BUY", '
            '"quantity": 2, "rationale": "hello"}'
            "]}",
            encoding="utf-8",
        )
        _, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(bad)])
    assert code == 1
    assert "duplicate" in stderr


def test_empty_rationale_produces_operator_readable_error() -> None:
    """SignalIntent invariants (e.g. non-empty rationale) flow through as
    operator-readable diagnostics rather than tracebacks."""
    with tempfile.TemporaryDirectory() as raw_temp:
        bad = Path(raw_temp) / "empty_rationale.json"
        bad.write_text(
            '{"signals": [{"intent_id": "x", "symbol": "AAPL", "side": "BUY", '
            '"quantity": 1, "rationale": ""}]}',
            encoding="utf-8",
        )
        _, stderr, code = _run_cli(["--source", "signals_json", "--signals-file", str(bad)])
    assert code == 1
    assert "is invalid" in stderr
    assert "Traceback" not in stderr


# ---------------------------------------------------------------------------
# 8. CLI usage errors
# ---------------------------------------------------------------------------


def test_signals_file_without_signals_json_source_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        path = Path(raw_temp) / "ideas.json"
        path.write_text('{"signals": []}', encoding="utf-8")
        _, stderr, code = _run_cli(["--source", "synthetic", "--signals-file", str(path)])
    assert code == 2
    assert "signals_json" in stderr


def test_signals_json_source_requires_signals_file() -> None:
    _, stderr, code = _run_cli(["--source", "signals_json"])
    assert code == 2
    assert "--signals-file is required" in stderr


# ---------------------------------------------------------------------------
# 9. Default no-flag synthetic stdout unchanged
# ---------------------------------------------------------------------------


def test_default_no_flag_synthetic_stdout_unchanged() -> None:
    # The signals_json source choice is purely additive; the default
    # synthetic dry-run output is unchanged.
    stdout, _, code = _run_cli([])
    assert code is None
    assert "daily_report:" in stdout
    assert "decisions: 3 total, 2 would_trade, 1 would_skip" in stdout


# ---------------------------------------------------------------------------
# Pure loader unit tests (no CLI)
# ---------------------------------------------------------------------------


def test_load_signals_returns_typed_signal_intents_in_order() -> None:
    loaded = load_signals(_TWO_IDEAS)
    assert len(loaded) == 2
    assert loaded[0].intent_id == "exp-1-aapl-long"
    assert loaded[0].symbol == "AAPL"
    assert loaded[0].side is SignalSide.BUY
    assert loaded[0].quantity == 10
    assert loaded[1].intent_id == "exp-2-tsla-short"
    assert loaded[1].side is SignalSide.SELL


def test_load_signals_accepts_empty_signals_array() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        path = Path(raw_temp) / "empty.json"
        path.write_text('{"signals": []}', encoding="utf-8")
        loaded = load_signals(path)
    assert loaded == ()


def test_load_signals_rejects_top_level_list() -> None:
    with tempfile.TemporaryDirectory() as raw_temp:
        path = Path(raw_temp) / "list.json"
        path.write_text("[]", encoding="utf-8")
        raised: BaseException | None = None
        try:
            load_signals(path)
        except SignalsFileSchemaError as exc:
            raised = exc
    assert isinstance(raised, SignalsFileSchemaError)
    assert "top-level value" in str(raised)
