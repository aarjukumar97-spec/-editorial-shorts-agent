from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, String, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from editorial_shorts_agent.domain import DiscoveryRun, utc_now


class Base(DeclarativeBase):
    pass


class DiscoveryRunRow(Base):
    __tablename__ = "discovery_runs"

    run_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    region: Mapped[str] = mapped_column(String(8), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    provider: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Database:
    def __init__(self, database_url: str) -> None:
        options = {}
        if ":memory:" in database_url:
            options = {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
        self.engine: AsyncEngine = create_async_engine(database_url, **options)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_schema(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()


class SqlAlchemyDiscoveryRunRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def save(self, run: DiscoveryRun) -> None:
        now = utc_now()
        payload = run.model_dump(mode="json")
        async with self._sessions() as session:
            row = await session.get(DiscoveryRunRow, str(run.run_id))
            if row is None:
                row = DiscoveryRunRow(
                    run_id=str(run.run_id),
                    region=run.region.value,
                    status=run.status.value,
                    provider=run.provider,
                    payload=payload,
                    created_at=run.requested_at,
                    updated_at=now,
                )
                session.add(row)
            else:
                row.region = run.region.value
                row.status = run.status.value
                row.provider = run.provider
                row.payload = payload
                row.updated_at = now
            await session.commit()

    async def get(self, run_id: UUID) -> DiscoveryRun | None:
        async with self._sessions() as session:
            statement = select(DiscoveryRunRow).where(
                DiscoveryRunRow.run_id == str(run_id)
            )
            row = (await session.execute(statement)).scalar_one_or_none()
            if row is None:
                return None
            return DiscoveryRun.model_validate(row.payload)
