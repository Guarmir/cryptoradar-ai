from abc import ABC, abstractmethod

from app.ai.market_domain import (
    MarketDomain,
)
from app.ai.market_overview_snapshot import (
    MarketOverviewSnapshot,
)


class MarketOverviewProvider(
    ABC
):
    @property
    @abstractmethod
    def domain(
        self,
    ) -> MarketDomain:
        raise NotImplementedError

    @abstractmethod
    def fetch(
        self,
    ) -> MarketOverviewSnapshot:
        raise NotImplementedError