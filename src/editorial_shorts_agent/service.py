from __future__ import annotations

from uuid import UUID

from editorial_shorts_agent.domain import (
    REGIONAL_LANGUAGE,
    AuditSource,
    DiscoveryRun,
    Region,
    RunError,
    RunStatus,
    utc_now,
)
from editorial_shorts_agent.ports import (
    DiscoveryRunRepository,
    OpportunityScorer,
    TopicClusterer,
    TrendProvider,
)
from editorial_shorts_agent.providers.youtube import TrendProviderError


class DiscoveryService:
    def __init__(
        self,
        *,
        provider: TrendProvider,
        clusterer: TopicClusterer,
        scorer: OpportunityScorer,
        repository: DiscoveryRunRepository,
    ) -> None:
        self._provider = provider
        self._clusterer = clusterer
        self._scorer = scorer
        self._repository = repository

    @property
    def provider_name(self) -> str:
        return self._provider.name

    async def create_run(self, *, region: Region, max_results: int) -> DiscoveryRun:
        run = DiscoveryRun(
            region=region,
            language=REGIONAL_LANGUAGE[region],
            provider=self._provider.name,
        )
        run.record(
            stage="discovery",
            source=AuditSource.POLICY,
            message="Regional editorial language selected.",
            metadata={"region": region.value, "language": run.language.value},
        )
        await self._repository.save(run)

        try:
            run.status = RunStatus.FETCHING
            run.record(
                stage="discovery",
                source=AuditSource.TOOL,
                message="Fetching regional most-popular video snapshot.",
                metadata={"provider": self._provider.name, "max_results": max_results},
            )
            await self._repository.save(run)
            videos = await self._provider.fetch_most_popular(region, max_results)
            run.video_count = len(videos)
            run.record(
                stage="discovery",
                source=AuditSource.TOOL,
                message="Regional video snapshot fetched.",
                metadata={"video_count": len(videos)},
            )

            run.status = RunStatus.CLUSTERING
            await self._repository.save(run)
            seeds = self._clusterer.cluster(videos)
            run.record(
                stage="clustering",
                source=AuditSource.TOOL,
                message="Videos clustered into candidate topics.",
                metadata={"topic_count": len(seeds), "method": "lexical-baseline"},
            )

            run.status = RunStatus.SCORING
            await self._repository.save(run)
            run.opportunities = self._scorer.score(seeds)
            run.record(
                stage="scoring",
                source=AuditSource.VALIDATOR,
                message="Transparent opportunity score calculated.",
                metadata={"opportunity_count": len(run.opportunities)},
            )

            run.status = RunStatus.COMPLETED
            run.completed_at = utc_now()
            run.record(
                stage="discovery",
                source=AuditSource.POLICY,
                message="Discovery run completed without selecting or publishing a topic.",
            )
        except TrendProviderError as exc:
            self._fail(
                run,
                code=exc.code,
                message=str(exc),
                retryable=exc.retryable,
            )
        except Exception:
            self._fail(
                run,
                code="DISCOVERY_FAILED",
                message="The discovery workflow failed unexpectedly.",
                retryable=False,
            )

        await self._repository.save(run)
        return run

    async def get_run(self, run_id: UUID) -> DiscoveryRun | None:
        return await self._repository.get(run_id)

    @staticmethod
    def _fail(
        run: DiscoveryRun,
        *,
        code: str,
        message: str,
        retryable: bool,
    ) -> None:
        run.status = RunStatus.FAILED
        run.completed_at = utc_now()
        run.error = RunError(code=code, message=message, retryable=retryable)
        run.record(
            stage="discovery",
            source=AuditSource.POLICY,
            message="Discovery run stopped with an explicit failure state.",
            metadata={"error_code": code, "retryable": retryable},
        )
