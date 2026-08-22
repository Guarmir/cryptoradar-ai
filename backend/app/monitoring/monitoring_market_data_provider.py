from abc import ABC, abstractmethod
from typing import Any, Mapping

from app.monitoring.monitoring_target import MonitoringTarget


class MonitoringMarketDataProvider(ABC):
    @abstractmethod
    def fetch_market_data(
        self,
        target: MonitoringTarget,
    ) -> Mapping[str, Any]:
        raise NotImplementedError