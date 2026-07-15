from __future__ import annotations

from typing import Protocol
from uuid import UUID

from editorial_shorts_agent.clustering import TopicSeed
from editorial_shorts_agent.domain import DiscoveryRun, Region, TopicOpportunity, TrendVideo


class TrendProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def fetch_most_popular(self, region: Region, max_results: int) -> list[TrendVideo]: ...


class TopicClusterer(Protocol):
    def cluster(self, videos: list[TrendVideo]) -> list[TopicSeed]: ...


class OpportunityScorer(Protocol):
    def score(self, seeds: list[TopicSeed]) -> list[TopicOpportunity]: ...


class DiscoveryRunRepository(Protocol):
    async def save(self, run: DiscoveryRun) -> None: ...

    async def get(self, run_id: UUID) -> DiscoveryRun | None: ...
