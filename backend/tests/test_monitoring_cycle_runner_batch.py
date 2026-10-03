from app.monitoring.monitoring_cycle_runner import (
    MonitoringCycleRunner,
)


class _FakeBatchMonitoringService:
    def __init__(self):
        self.registered_symbols = (
            "BTC",
            "ETH",
            "SOL",
        )

        self.batch_fetch_count = 0
        self.observed_symbols = []

    def fetch_market_data_batch(
        self,
        symbols,
    ):
        self.batch_fetch_count += 1

        assert tuple(symbols) == (
            "BTC",
            "ETH",
            "SOL",
        )

        return {
            "BTC": {
                "id": "bitcoin",
                "current_price": 100,
            },
            "ETH": {
                "id": "ethereum",
                "current_price": 200,
            },
            "SOL": {
                "id": "solana",
                "current_price": 300,
            },
        }

    def observe_market_data(
        self,
        symbol,
        market_data,
    ):
        self.observed_symbols.append(
            (
                symbol,
                market_data["current_price"],
            )
        )

        return {
            "symbol": symbol,
        }


def test_runner_uses_single_batch_fetch_for_registered_assets():
    service = _FakeBatchMonitoringService()

    runner = MonitoringCycleRunner(
        service=service,
    )

    runner.run_once()

    assert service.batch_fetch_count == 1

    assert service.observed_symbols == [
        ("BTC", 100),
        ("ETH", 200),
        ("SOL", 300),
    ]