from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Region(StrEnum):
    INDIA = "IN"
    UNITED_STATES = "US"


class EditorialLanguage(StrEnum):
    HINGLISH = "hi-Latn"
    ENGLISH_US = "en-US"


REGIONAL_LANGUAGE: dict[Region, EditorialLanguage] = {
    Region.INDIA: EditorialLanguage.HINGLISH,
    Region.UNITED_STATES: EditorialLanguage.ENGLISH_US,
}


class RunStatus(StrEnum):
    CREATED = "CREATED"
    FETCHING = "FETCHING"
    CLUSTERING = "CLUSTERING"
    SCORING = "SCORING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TrendStage(StrEnum):
    SINGLE_SOURCE = "SINGLE_SOURCE"
    EMERGING_CANDIDATE = "EMERGING_CANDIDATE"
    SURGING_CANDIDATE = "SURGING_CANDIDATE"
    MULTI_SOURCE = "MULTI_SOURCE"
    SATURATED_CANDIDATE = "SATURATED_CANDIDATE"


class AuditSource(StrEnum):
    TOOL = "TOOL"
    MODEL = "MODEL"
    POLICY = "POLICY"
    VALIDATOR = "VALIDATOR"


class ClipPurpose(StrEnum):
    DIRECT_TOPIC_CLIP = "DIRECT_TOPIC_CLIP"
    EDITORIAL_EXCERPT = "EDITORIAL_EXCERPT"
    ILLUSTRATIVE_BROLL = "ILLUSTRATIVE_BROLL"


class ClipRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKED = "BLOCKED"


class AcquisitionStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditEvent(StrictModel):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=utc_now)
    stage: str = Field(min_length=1, max_length=80)
    source: AuditSource
    message: str = Field(min_length=1, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrendVideo(StrictModel):
    video_id: str = Field(min_length=1, max_length=128)
    region: Region
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=10_000)
    channel_id: str = Field(min_length=1, max_length=128)
    channel_title: str = Field(min_length=1, max_length=300)
    published_at: datetime
    observed_at: datetime = Field(default_factory=utc_now)
    view_count: int = Field(default=0, ge=0)
    like_count: int = Field(default=0, ge=0)
    comment_count: int = Field(default=0, ge=0)
    duration_seconds: int = Field(default=0, ge=0)
    category_id: str | None = Field(default=None, max_length=32)
    tags: list[str] = Field(default_factory=list, max_length=100)
    source_url: str = Field(min_length=1, max_length=2_000)


class OpportunityScore(StrictModel):
    total: float = Field(ge=0, le=100)
    estimated_view_velocity: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    cross_channel_spread: float = Field(ge=0, le=1)
    regional_popularity: float = Field(ge=0, le=1)
    audience_fit: float = Field(ge=0, le=1)
    asset_feasibility: float = Field(ge=0, le=1)
    saturation_penalty: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)


class TopicOpportunity(StrictModel):
    topic_id: UUID
    rank: int = Field(default=0, ge=0)
    region: Region
    label: str = Field(min_length=1, max_length=300)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    stage: TrendStage
    unique_channel_count: int = Field(ge=1)
    total_view_count: int = Field(ge=0)
    source_videos: list[TrendVideo] = Field(min_length=1)
    score: OpportunityScore


class RunError(StrictModel):
    code: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=500)
    retryable: bool = False


class DiscoveryRun(StrictModel):
    run_id: UUID = Field(default_factory=uuid4)
    region: Region
    language: EditorialLanguage
    provider: str = Field(min_length=1, max_length=100)
    status: RunStatus = RunStatus.CREATED
    requested_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None
    video_count: int = Field(default=0, ge=0)
    opportunities: list[TopicOpportunity] = Field(default_factory=list)
    audit: list[AuditEvent] = Field(default_factory=list)
    error: RunError | None = None

    def record(
        self,
        *,
        stage: str,
        source: AuditSource,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.audit.append(
            AuditEvent(
                stage=stage,
                source=source,
                message=message,
                metadata=metadata or {},
            )
        )


class SourceReference(StrictModel):
    source_id: UUID = Field(default_factory=uuid4)
    source_url: str = Field(min_length=1, max_length=2_000)
    creator: str = Field(min_length=1, max_length=300)
    source_title: str = Field(min_length=1, max_length=500)
    retrieved_at: datetime = Field(default_factory=utc_now)
    source_timestamp_seconds: float = Field(ge=0)


class EditorialClipCandidate(StrictModel):
    clip_id: UUID = Field(default_factory=uuid4)
    source: SourceReference
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    narration_beat_id: str = Field(min_length=1, max_length=128)
    purpose: ClipPurpose
    risk: ClipRisk
    acquisition_status: AcquisitionStatus = AcquisitionStatus.CANDIDATE
    relevance_reason: str = Field(min_length=1, max_length=500)
    replacement_candidate_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_timing(self) -> EditorialClipCandidate:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("end_seconds must be greater than start_seconds")
        return self

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds
