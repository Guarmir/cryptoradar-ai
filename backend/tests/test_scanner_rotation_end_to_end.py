
from app.early_movement.scanner import (
    EarlyMovementScanner,
)
from app.early_movement.scanner.scanner_chart_loader import (
    EarlyMovementScannerChartLoader,
)
from app.early_movement.scanner.scanner_rotation_bridge import (
    EarlyMovementScannerRotationBridge,
)


class FakeCandidate:
    def __init__(self, coin_id):
        self.coin_id = coin_id


class FakeMarketProvider:
    def fetch(self):
        return tuple(
            FakeCandidate(f"coin-{index}")
            for index in range(20)
        )


class FakeSelector:
    def select(self, assets, *, limit):
        return tuple(assets[:limit])


class FakeAnalysisResult:
    def __init__(self, candidate, analysis):
        self.candidate = candidate
        self.analysis = analysis


class LoaderBackedAnalyzer:
    def __init__(self, loader):
        self.loader = loader

    def analyze_candidates(self, candidates):
        results = []

        for candidate in candidates:
            chart = self.loader(
                candidate.coin_id,
                7,
            )

            results.append(
                FakeAnalysisResult(
                    candidate,
                    (
                        object()
                        if chart.get("prices")
                        else None
                    ),
                )
            )

        return tuple(results)


class FakeRanker:
    def rank(self, results, *, limit):
        return tuple(
            result
            for result in results
            if result.analysis is not None
        )[:limit]


def test_rotation_scanner_loader_multiple_cycles():
    acquired = []

    bridge = EarlyMovementScannerRotationBridge(
        acquisition_budget=4,
        priority_slots=1,
    )

    def fake_chart_loader(coin_id, days):
        acquired.append(coin_id)
        return {"prices": [[1, 100.0]]}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=fake_chart_loader,
        cache_loader=lambda coin_id, days: None,
        request_budget=4,
        on_chart_result=bridge.on_chart_result,
    )

    scanner = EarlyMovementScanner(
        market_provider=FakeMarketProvider(),
        candidate_selector=FakeSelector(),
        deep_analyzer=LoaderBackedAnalyzer(loader),
        result_ranker=FakeRanker(),
        candidate_arranger=bridge.arrange,
    )

    for _ in range(5):
        loader.reset_budget()
        result = scanner.scan()

        assert result.candidate_count == 20
        assert result.successful_analysis_count == 4
        assert loader.stats.acquisition_attempts == 4
        assert loader.stats.budget_exhausted == 16

    assert len(acquired) == 20
    assert len(set(acquired)) == 20

    
def test_rotation_continues_after_chart_failures():
    acquired = []

    bridge = EarlyMovementScannerRotationBridge(
        acquisition_budget=4,
        priority_slots=1,
    )

    def fake_chart_loader(coin_id, days):
        acquired.append(coin_id)

        if coin_id in {"coin-1", "coin-2"}:
            raise RuntimeError(
                "Falha simulada de aquisição"
            )

        return {
            "prices": [[1, 100.0]],
        }

    loader = EarlyMovementScannerChartLoader(
        chart_loader=fake_chart_loader,
        cache_loader=lambda coin_id, days: None,
        request_budget=4,
        on_chart_result=bridge.on_chart_result,
    )

    class SafeLoaderBackedAnalyzer:
        def analyze_candidates(self, candidates):
            results = []

            for candidate in candidates:
                try:
                    chart = loader(
                        candidate.coin_id,
                        7,
                    )
                except RuntimeError:
                    chart = {"prices": []}

                results.append(
                    FakeAnalysisResult(
                        candidate,
                        (
                            object()
                            if chart.get("prices")
                            else None
                        ),
                    )
                )

            return tuple(results)

    scanner = EarlyMovementScanner(
        market_provider=FakeMarketProvider(),
        candidate_selector=FakeSelector(),
        deep_analyzer=SafeLoaderBackedAnalyzer(),
        result_ranker=FakeRanker(),
        candidate_arranger=bridge.arrange,
    )

    for _ in range(5):
        loader.reset_budget()
        result = scanner.scan()

        assert result.candidate_count == 20
        assert loader.stats.acquisition_attempts == 4
        assert loader.stats.budget_exhausted == 16

    assert len(acquired) == 20

    assert len(set(acquired)) >= 15

    assert any(
        coin_id not in {"coin-1", "coin-2"}
        for coin_id in acquired
    )



def test_followup_receives_chart_priority_across_cycles():
    from types import SimpleNamespace

    from app.early_movement.scanner.scanner_active_followup import (
        EarlyMovementScannerActiveFollowup,
    )

    acquired = []

    bridge = EarlyMovementScannerRotationBridge(
        acquisition_budget=4,
        priority_slots=1,
    )

    def fake_chart_loader(coin_id, days):
        acquired.append(coin_id)
        return {"prices": [[1, 100.0]]}

    loader = EarlyMovementScannerChartLoader(
        chart_loader=fake_chart_loader,
        cache_loader=lambda coin_id, days: None,
        request_budget=4,
        on_chart_result=bridge.on_chart_result,
    )

    class FollowupSelector:
        def select(
            self,
            assets,
            *,
            limit,
            followup_ids=(),
        ):
            return tuple(assets[:limit])

    class FollowupRanker:
        def rank(self, results, *, limit):
            relevant = [
                result
                for result in results
                if (
                    result.analysis is not None
                    and result.candidate.coin_id == "coin-19"
                )
            ]

            if relevant:
                return (
                    SimpleNamespace(result=relevant[0]),
                )

            return ()

    followup = EarlyMovementScannerActiveFollowup()

    scanner = EarlyMovementScanner(
        market_provider=FakeMarketProvider(),
        candidate_selector=FollowupSelector(),
        deep_analyzer=LoaderBackedAnalyzer(loader),
        result_ranker=FollowupRanker(),
        candidate_arranger=bridge.arrange,
        active_followup=followup,
    )

    # Primeiro ciclo: aquisição inicial e descoberta.
    loader.reset_budget()
    scanner.scan()

    # Simula um ativo relevante já identificado.
    followup.observe(("coin-19",))

    first_cycle_acquisitions = len(acquired)

    # Segundo ciclo: o ativo acompanhado deve
    # receber prioridade na aquisição.
    loader.reset_budget()
    scanner.scan()

    second_cycle_acquisitions = acquired[
        first_cycle_acquisitions:
    ]

    assert "coin-19" in second_cycle_acquisitions
    assert len(second_cycle_acquisitions) <= 4
    assert loader.stats.acquisition_attempts <= 4
