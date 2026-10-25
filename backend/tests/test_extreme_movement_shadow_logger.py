import json
import logging

from app.early_movement.extreme_movement.extreme_movement_assessment import (
    ExtremeMovementAssessment,
)
from app.early_movement.extreme_movement.extreme_movement_analysis_adapter import (
    ExtremeMovementAnalysisEntry,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_logger import (
    ExtremeMovementShadowLogger,
)
from app.early_movement.extreme_movement.extreme_movement_shadow_runner import (
    ExtremeMovementShadowResult,
)


class RecordingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def make_logger():
    logger = logging.getLogger(
        "test.extreme_movement.shadow"
    )
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = RecordingHandler()
    logger.addHandler(handler)

    return ExtremeMovementShadowLogger(logger=logger), handler, logger


def make_result(entries=()):
    return ExtremeMovementShadowResult(
        analyzed_count=4,
        evaluated_count=len(entries),
        extreme_acceleration_count=sum(
            e.assessment.state == "extreme_acceleration"
            for e in entries
        ),
        movement_pressure_count=sum(
            e.assessment.state == "movement_pressure"
            for e in entries
        ),
        possible_reversal_count=sum(
            e.assessment.state == "possible_reversal"
            for e in entries
        ),
        insufficient_evidence_count=sum(
            e.assessment.state == "insufficient_evidence"
            for e in entries
        ),
        entries=entries,
    )


def test_logger_records_cycle_summary():
    shadow_logger, handler, logger = make_logger()

    try:
        shadow_logger.log(make_result())

        assert len(handler.messages) == 1

        payload = json.loads(handler.messages[0])

        assert payload["event"] == "extreme_movement_shadow_cycle"
        assert payload["analyzed_count"] == 4
        assert payload["evaluated_count"] == 0
        assert payload["assets"] == []
        assert "timestamp" in payload
    finally:
        logger.removeHandler(handler)


def test_logger_records_asset_assessment():
    shadow_logger, handler, logger = make_logger()

    entry = ExtremeMovementAnalysisEntry(
        coin_id="bitcoin",
        symbol="BTC",
        name="Bitcoin",
        assessment=ExtremeMovementAssessment(
            state="extreme_acceleration",
            direction="up",
            relevance_score=85.0,
            supporting_evidence_count=3,
        ),
    )

    try:
        shadow_logger.log(make_result((entry,)))

        payload = json.loads(handler.messages[0])
        asset = payload["assets"][0]

        assert payload["extreme_acceleration_count"] == 1
        assert asset["coin_id"] == "bitcoin"
        assert asset["symbol"] == "BTC"
        assert asset["state"] == "extreme_acceleration"
        assert asset["direction"] == "up"
        assert asset["relevance_score"] == 85.0
        assert asset["supporting_evidence_count"] == 3
    finally:
        logger.removeHandler(handler)


def test_logger_records_possible_reversal():
    shadow_logger, handler, logger = make_logger()

    entry = ExtremeMovementAnalysisEntry(
        coin_id="example",
        symbol="EXM",
        name="Example",
        assessment=ExtremeMovementAssessment(
            state="possible_reversal",
            direction="down",
            relevance_score=72.0,
            supporting_evidence_count=2,
        ),
    )

    try:
        shadow_logger.log(make_result((entry,)))

        payload = json.loads(handler.messages[0])

        assert payload["possible_reversal_count"] == 1
        assert payload["assets"][0]["state"] == "possible_reversal"
        assert payload["assets"][0]["direction"] == "down"
    finally:
        logger.removeHandler(handler)