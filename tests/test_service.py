from editorial_shorts_agent.clustering import LexicalTopicClusterer
from editorial_shorts_agent.domain import EditorialLanguage, Region, RunStatus
from editorial_shorts_agent.providers.fixture import FixtureTrendProvider
from editorial_shorts_agent.providers.youtube import TrendProviderError
from editorial_shorts_agent.repository import Database, SqlAlchemyDiscoveryRunRepository
from editorial_shorts_agent.scoring import WeightedOpportunityScorer
from editorial_shorts_agent.service import DiscoveryService


async def _service(provider):
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_schema()
    repository = SqlAlchemyDiscoveryRunRepository(database.sessions)
    service = DiscoveryService(
        provider=provider,
        clusterer=LexicalTopicClusterer(),
        scorer=WeightedOpportunityScorer(),
        repository=repository,
    )
    return database, service


async def test_india_run_uses_hinglish_and_is_persisted() -> None:
    database, service = await _service(FixtureTrendProvider())

    run = await service.create_run(region=Region.INDIA, max_results=25)
    persisted = await service.get_run(run.run_id)
    await database.close()

    assert run.status is RunStatus.COMPLETED
    assert run.language is EditorialLanguage.HINGLISH
    assert run.video_count == 4
    assert run.opportunities
    assert persisted == run
    assert {event.source.value for event in run.audit} >= {"TOOL", "POLICY", "VALIDATOR"}


class FailingProvider:
    @property
    def name(self) -> str:
        return "failing-test-provider"

    async def fetch_most_popular(self, region: Region, max_results: int):
        raise TrendProviderError("UPSTREAM_DOWN", "Upstream is unavailable.", retryable=True)


async def test_provider_failure_is_explicit_and_persisted() -> None:
    database, service = await _service(FailingProvider())

    run = await service.create_run(region=Region.UNITED_STATES, max_results=10)
    persisted = await service.get_run(run.run_id)
    await database.close()

    assert run.status is RunStatus.FAILED
    assert run.error is not None
    assert run.error.code == "UPSTREAM_DOWN"
    assert run.error.retryable is True
    assert persisted == run
