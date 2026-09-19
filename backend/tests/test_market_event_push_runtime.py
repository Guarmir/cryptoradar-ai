from unittest.mock import patch

import pytest

from app.monitoring.market_event_evaluator import (
    MarketEventEvaluator,
)
from app.monitoring.monitoring_runtime import (
    MonitoringRuntime,
)
from app.monitoring.monitoring_runtime_config import (
    MonitoringRuntimeConfig,
)
from app.monitoring.monitoring_runtime_factory import (
    build_monitoring_runtime,
)
from app.push.market_event_push_runtime_config import (
    MarketEventPushRuntimeConfig,
)


def test_market_event_push_is_disabled_by_default():
    config = (
        MarketEventPushRuntimeConfig
        .from_environment(
            {}
        )
    )

    assert not config.enabled
    assert config.minimum_price_change_percent == 1.0
    assert config.cooldown_seconds == 300.0
    assert config.maximum_observation_gap_seconds == 180.0


def test_disabled_configuration_ignores_tuning_values():
    config = (
        MarketEventPushRuntimeConfig
        .from_environment(
            {
                "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                    "false",
                "CRYPTORADAR_MARKET_EVENT_MINIMUM_PRICE_CHANGE_PERCENT":
                    "invalid",
                "CRYPTORADAR_MARKET_EVENT_PUSH_COOLDOWN_SECONDS":
                    "invalid",
                "CRYPTORADAR_MARKET_EVENT_MAX_OBSERVATION_GAP_SECONDS":
                    "invalid",
            }
        )
    )

    assert not config.enabled
    assert config.minimum_price_change_percent == 1.0
    assert config.cooldown_seconds == 300.0
    assert config.maximum_observation_gap_seconds == 180.0


def test_parses_enabled_configuration():
    config = (
        MarketEventPushRuntimeConfig
        .from_environment(
            {
                "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                    "true",
                "CRYPTORADAR_DATABASE_URL":
                    "postgresql://test",
                "CRYPTORADAR_PUSH_SCOPE":
                    "push-test",
                "CRYPTORADAR_MARKET_EVENT_MINIMUM_PRICE_CHANGE_PERCENT":
                    "1.5",
                "CRYPTORADAR_MARKET_EVENT_PUSH_COOLDOWN_SECONDS":
                    "600",
                "CRYPTORADAR_MARKET_EVENT_MAX_OBSERVATION_GAP_SECONDS":
                    "180",
            }
        )
    )

    assert config.enabled
    assert config.database_url == "postgresql://test"
    assert config.scope_key == "push-test"
    assert config.minimum_price_change_percent == 1.5
    assert config.cooldown_seconds == 600.0
    assert config.maximum_observation_gap_seconds == 180.0


def test_enabled_configuration_requires_database_url():
    with pytest.raises(ValueError):
        (
            MarketEventPushRuntimeConfig
            .from_environment(
                {
                    "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                        "true",
                    "CRYPTORADAR_PUSH_SCOPE":
                        "push-test",
                }
            )
        )


def test_enabled_configuration_requires_push_scope():
    with pytest.raises(ValueError):
        (
            MarketEventPushRuntimeConfig
            .from_environment(
                {
                    "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                        "true",
                    "CRYPTORADAR_DATABASE_URL":
                        "postgresql://test",
                }
            )
        )


def test_enabled_configuration_rejects_invalid_minimum_change():
    with pytest.raises(ValueError):
        (
            MarketEventPushRuntimeConfig
            .from_environment(
                {
                    "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                        "true",
                    "CRYPTORADAR_DATABASE_URL":
                        "postgresql://test",
                    "CRYPTORADAR_PUSH_SCOPE":
                        "push-test",
                    "CRYPTORADAR_MARKET_EVENT_MINIMUM_PRICE_CHANGE_PERCENT":
                        "0",
                }
            )
        )


def test_enabled_configuration_rejects_invalid_cooldown():
    with pytest.raises(ValueError):
        (
            MarketEventPushRuntimeConfig
            .from_environment(
                {
                    "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                        "true",
                    "CRYPTORADAR_DATABASE_URL":
                        "postgresql://test",
                    "CRYPTORADAR_PUSH_SCOPE":
                        "push-test",
                    "CRYPTORADAR_MARKET_EVENT_PUSH_COOLDOWN_SECONDS":
                        "-1",
                }
            )
        )


def test_enabled_configuration_rejects_invalid_maximum_gap():
    with pytest.raises(ValueError):
        (
            MarketEventPushRuntimeConfig
            .from_environment(
                {
                    "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED":
                        "true",
                    "CRYPTORADAR_DATABASE_URL":
                        "postgresql://test",
                    "CRYPTORADAR_PUSH_SCOPE":
                        "push-test",
                    "CRYPTORADAR_MARKET_EVENT_MAX_OBSERVATION_GAP_SECONDS":
                        "0",
                }
            )
        )


def test_runtime_factory_keeps_market_push_disabled(
    monkeypatch,
):
    monkeypatch.delenv(
        "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED",
        raising=False,
    )

    monitoring_config = (
        MonitoringRuntimeConfig(
            enabled=True,
            database_url="postgresql://test",
            scope_key="monitoring-test",
            interval_seconds=60,
        )
    )

    with patch(
        "app.monitoring.monitoring_runtime_factory."
        "MonitoringCycleRunner"
    ) as runner_class:
        runner_class.return_value = object()

        runtime = build_monitoring_runtime(
            monitoring_config,
        )

        assert isinstance(
            runtime,
            MonitoringRuntime,
        )

        runner_arguments = (
            runner_class.call_args.kwargs
        )

        assert (
            runner_arguments[
                "market_event_evaluator"
            ]
            is None
        )

        assert (
            runner_arguments[
                "market_event_callback"
            ]
            is None
        )


def test_runtime_factory_wires_enabled_market_push(
    monkeypatch,
):
    monkeypatch.setenv(
        "CRYPTORADAR_MARKET_EVENT_PUSH_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "CRYPTORADAR_DATABASE_URL",
        "postgresql://push-test",
    )

    monkeypatch.setenv(
        "CRYPTORADAR_PUSH_SCOPE",
        "push-test",
    )

    monkeypatch.setenv(
        "CRYPTORADAR_MARKET_EVENT_MINIMUM_PRICE_CHANGE_PERCENT",
        "1.5",
    )

    monkeypatch.setenv(
        "CRYPTORADAR_MARKET_EVENT_PUSH_COOLDOWN_SECONDS",
        "600",
    )

    monkeypatch.setenv(
        "CRYPTORADAR_MARKET_EVENT_MAX_OBSERVATION_GAP_SECONDS",
        "180",
    )

    monitoring_config = (
        MonitoringRuntimeConfig(
            enabled=True,
            database_url=(
                "postgresql://monitoring-test"
            ),
            scope_key="monitoring-test",
            interval_seconds=60,
        )
    )

    with patch(
        "app.monitoring.monitoring_runtime_factory."
        "MonitoringCycleRunner"
    ) as runner_class:
        runner_class.return_value = object()

        runtime = build_monitoring_runtime(
            monitoring_config,
        )

        assert isinstance(
            runtime,
            MonitoringRuntime,
        )

        runner_arguments = (
            runner_class.call_args.kwargs
        )

        evaluator = runner_arguments[
            "market_event_evaluator"
        ]

        callback = runner_arguments[
            "market_event_callback"
        ]

        assert isinstance(
            evaluator,
            MarketEventEvaluator,
        )

        assert (
            evaluator.minimum_price_change_percent
            == 1.5
        )

        assert (
            evaluator.maximum_observation_gap_seconds
            == 180.0
        )

        assert callable(
            callback,
        )