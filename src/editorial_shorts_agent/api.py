from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from editorial_shorts_agent.clustering import LexicalTopicClusterer
from editorial_shorts_agent.config import Settings, TrendProviderName
from editorial_shorts_agent.domain import DiscoveryRun, Region
from editorial_shorts_agent.ports import TrendProvider
from editorial_shorts_agent.providers.fixture import FixtureTrendProvider
from editorial_shorts_agent.providers.youtube import YouTubeTrendProvider
from editorial_shorts_agent.repository import Database, SqlAlchemyDiscoveryRunRepository
from editorial_shorts_agent.scoring import WeightedOpportunityScorer
from editorial_shorts_agent.service import DiscoveryService


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateDiscoveryRunRequest(ApiModel):
    region: Region
    max_results: int | None = Field(default=None, ge=1, le=50)


class HealthResponse(ApiModel):
    status: str
    environment: str
    trend_provider: str


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    database: Database
    discovery_service: DiscoveryService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


ContainerDependency = Annotated[AppContainer, Depends(get_container)]


def _build_provider(settings: Settings) -> TrendProvider:
    if settings.trend_provider is TrendProviderName.FIXTURE:
        return FixtureTrendProvider()
    api_key = settings.youtube_api_key
    if api_key is None or not api_key.get_secret_value().strip():
        raise RuntimeError("ESA_YOUTUBE_API_KEY is required when ESA_TREND_PROVIDER=youtube")
    return YouTubeTrendProvider(
        api_key=api_key.get_secret_value(),
        timeout_seconds=settings.youtube_timeout_seconds,
    )


def create_app(
    *,
    settings: Settings | None = None,
    provider: TrendProvider | None = None,
    database: Database | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings()
    resolved_database = database or Database(resolved_settings.database_url)
    repository = SqlAlchemyDiscoveryRunRepository(resolved_database.sessions)
    resolved_provider = provider or _build_provider(resolved_settings)
    service = DiscoveryService(
        provider=resolved_provider,
        clusterer=LexicalTopicClusterer(),
        scorer=WeightedOpportunityScorer(),
        repository=repository,
    )
    container = AppContainer(
        settings=resolved_settings,
        database=resolved_database,
        discovery_service=service,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await container.database.create_schema()
        app.state.container = container
        yield
        await container.database.close()

    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        description=(
            "Region-aware trend discovery foundation for an auditable editorial Shorts workflow."
        ),
        lifespan=lifespan,
    )

    @app.get("/health", response_model=HealthResponse, tags=["operations"])
    async def health(current: ContainerDependency) -> HealthResponse:
        return HealthResponse(
            status="ok",
            environment=current.settings.environment,
            trend_provider=current.discovery_service.provider_name,
        )

    @app.post(
        "/v1/discovery-runs",
        response_model=DiscoveryRun,
        status_code=status.HTTP_201_CREATED,
        tags=["discovery"],
    )
    async def create_discovery_run(
        payload: CreateDiscoveryRunRequest,
        current: ContainerDependency,
    ) -> DiscoveryRun:
        max_results = payload.max_results or current.settings.youtube_max_results
        return await current.discovery_service.create_run(
            region=payload.region,
            max_results=max_results,
        )

    @app.get(
        "/v1/discovery-runs/{run_id}",
        response_model=DiscoveryRun,
        tags=["discovery"],
    )
    async def get_discovery_run(run_id: UUID, current: ContainerDependency) -> DiscoveryRun:
        run = await current.discovery_service.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Discovery run not found")
        return run

    return app
