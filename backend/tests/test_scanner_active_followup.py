
from app.early_movement.scanner.scanner_active_followup import (
    EarlyMovementScannerActiveFollowup,
)


def test_observe_registers_assets():
    followup = EarlyMovementScannerActiveFollowup()

    followup.observe(["akedo", "dash"])

    assert followup.active_ids() == (
        "akedo",
        "dash",
    )


def test_observe_ignores_duplicates_and_empty_ids():
    followup = EarlyMovementScannerActiveFollowup()

    followup.observe([
        "akedo",
        "akedo",
        " ",
        " dash ",
    ])

    assert followup.active_ids() == (
        "akedo",
        "dash",
    )


def test_followup_respects_capacity():
    followup = EarlyMovementScannerActiveFollowup(
        max_assets=2,
    )

    followup.observe(["akedo", "dash", "zama"])

    assert len(followup.active_ids()) == 2


def test_followup_expires_after_ttl():
    followup = EarlyMovementScannerActiveFollowup(
        ttl_cycles=2,
    )

    followup.observe(["akedo"])

    followup.advance_cycle()
    assert followup.active_ids() == ("akedo",)

    followup.advance_cycle()
    assert followup.active_ids() == ()
