from __future__ import annotations

import math
from datetime import UTC, datetime

from editorial_shorts_agent.clustering import TopicSeed
from editorial_shorts_agent.domain import OpportunityScore, TopicOpportunity, TrendStage


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalize_log(values: list[float]) -> list[float]:
    logged = [math.log1p(max(0.0, value)) for value in values]
    maximum = max(logged, default=0.0)
    if maximum == 0:
        return [0.0 for _ in values]
    return [value / maximum for value in logged]


class WeightedOpportunityScorer:
    """Transparent first-pass score; historical deltas and channel fit arrive in later phases."""

    def score(self, seeds: list[TopicSeed]) -> list[TopicOpportunity]:
        if not seeds:
            return []

        now = datetime.now(UTC)
        raw_velocities: list[float] = []
        raw_popularity: list[float] = []

        for seed in seeds:
            velocity = 0.0
            for video in seed.videos:
                age_hours = max((now - video.published_at).total_seconds() / 3600, 1.0)
                velocity += video.view_count / age_hours
            raw_velocities.append(velocity)
            raw_popularity.append(sum(video.view_count for video in seed.videos))

        velocities = _normalize_log(raw_velocities)
        popularity = _normalize_log(raw_popularity)
        opportunities: list[TopicOpportunity] = []

        for index, seed in enumerate(seeds):
            ages = [
                max((now - video.published_at).total_seconds() / 3600, 0.0) for video in seed.videos
            ]
            freshness = sum(math.exp(-age / 72) for age in ages) / len(ages)
            unique_channels = len({video.channel_id for video in seed.videos})
            spread = _bounded(unique_channels / 3)
            saturation = _bounded(max(0, len(seed.videos) - 6) / 10)

            # Neutral until a channel profile and asset-search feedback are wired in.
            audience_fit = 0.5
            asset_feasibility = 0.5
            total = 100 * _bounded(
                (0.32 * velocities[index])
                + (0.18 * freshness)
                + (0.18 * spread)
                + (0.14 * popularity[index])
                + (0.10 * audience_fit)
                + (0.08 * asset_feasibility)
                - (0.10 * saturation)
            )

            stage = self._stage(
                video_count=len(seed.videos),
                velocity=velocities[index],
                freshness=freshness,
                saturation=saturation,
            )
            reasons = [
                f"Observed across {unique_channels} channel(s).",
                f"Estimated view velocity component: {velocities[index]:.2f}.",
                f"Freshness component: {freshness:.2f}.",
                "Audience fit and asset feasibility are neutral until later workflow phases.",
            ]
            opportunities.append(
                TopicOpportunity(
                    topic_id=seed.topic_id,
                    region=seed.region,
                    label=seed.label,
                    keywords=seed.keywords,
                    stage=stage,
                    unique_channel_count=unique_channels,
                    total_view_count=int(raw_popularity[index]),
                    source_videos=seed.videos,
                    score=OpportunityScore(
                        total=round(total, 2),
                        estimated_view_velocity=round(velocities[index], 4),
                        freshness=round(freshness, 4),
                        cross_channel_spread=round(spread, 4),
                        regional_popularity=round(popularity[index], 4),
                        audience_fit=audience_fit,
                        asset_feasibility=asset_feasibility,
                        saturation_penalty=round(saturation, 4),
                        reasons=reasons,
                    ),
                )
            )

        opportunities.sort(key=lambda item: (-item.score.total, item.label))
        for rank, opportunity in enumerate(opportunities, start=1):
            opportunity.rank = rank
        return opportunities

    @staticmethod
    def _stage(
        *, video_count: int, velocity: float, freshness: float, saturation: float
    ) -> TrendStage:
        if video_count == 1:
            return TrendStage.SINGLE_SOURCE
        if saturation >= 0.5:
            return TrendStage.SATURATED_CANDIDATE
        if velocity >= 0.65 and freshness >= 0.45:
            return TrendStage.SURGING_CANDIDATE
        if freshness >= 0.55:
            return TrendStage.EMERGING_CANDIDATE
        return TrendStage.MULTI_SOURCE
