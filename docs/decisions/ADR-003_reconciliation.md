### Reconciliation Tolerance

**Formula**: `tolerance = max($10, 0.1% of NLV)`

| NLV | Tolerance |
|-----|-----------|
| $10,000 | $10 |
| $50,000 | $50 |
| $100,000 | $100 |
| $1,000,000 | $1,000 |

**Rationale**: $10 minimum covers IB fees, rounding errors. 0.1% covers slippage, FX rounding, order fill variations.

### Reconciliation Schedule

| Time | Frequency | Details |
|------|-----------|---------|
| Every hour | 24/day | Full position + cash reconciliation |
| Daily 22:00 UTC | 1/day | Full detailed report (logs to DB) |
| Weekly (Mon 09:00 UTC) | 1/week | Deep audit (compare transaction history) |

---

## Rationale

Why hourly auto-daemon?

- **Early detection**: Mismatches caught within 60 min, not hours or days
- **Automated**: Solo operator can't manually reconcile daily
- **Audit trail**: 24 hourly reconciliation logs per day (excellent for postmortems)
- **Fail-safe**: Kill switch auto-triggers on mismatch (prevents bad decisions)

---

## Follow-Up Actions

| Action | Timeline |
|--------|----------|
| Implement reconcile_daemon.py | Phase 2 |
| Create launchd .plist configuration | Phase 2 |
| Test with historical IB data | Phase 2 |
| Define reconciliation tolerance precisely | Phase 2 |
| Add to daily report template | Phase 2 |

---

## Approval

**Decision Made By**: Kevin Heaney (2026-05-10)  
**Status**: Accepted  
**Implementation**: Phase 2
