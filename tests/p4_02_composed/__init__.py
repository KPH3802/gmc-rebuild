"""P4-02 composed-fixture tests.

Test-only package marker for the P4-02 composed-fixture test that
exercises the three already-merged in-memory fakes
(``InMemoryHeartbeat``, ``InMemoryKillSwitch``,
``InMemoryReconciliation``) together against their abstract
:class:`typing.Protocol` boundaries declared in
:mod:`gmc_rebuild.risk` (``HeartbeatProtocol``, ``KillSwitchProtocol``,
``ReconciliationProtocol``).

Authorization: ``governance/authorizations/2026-05-14_p4-02.md``.

This package introduces no runtime behaviour, no ``__main__`` entry
point, no daemon, no scheduler, no broker / market-data / order /
strategy / persistence / deployment / env-var / secrets / network /
``time.sleep`` / concrete protocol implementation, no re-export of
any merged Phase 3 fixture from any runtime path, and no new
``src/**`` directory. Its sole consumer is :mod:`pytest`.
"""
