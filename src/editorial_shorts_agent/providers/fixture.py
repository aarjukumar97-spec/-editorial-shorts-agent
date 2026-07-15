from __future__ import annotations

from datetime import timedelta

from editorial_shorts_agent.domain import Region, TrendVideo, utc_now


class FixtureTrendProvider:
    """Repeatable local demo input. Production configuration must select YouTube."""

    @property
    def name(self) -> str:
        return "fixture"

    async def fetch_most_popular(self, region: Region, max_results: int) -> list[TrendVideo]:
        observed_at = utc_now()
        fixtures = self._india(observed_at) if region is Region.INDIA else self._us(observed_at)
        return fixtures[:max_results]

    @staticmethod
    def _india(observed_at):
        return [
            TrendVideo(
                video_id="in-ai-1",
                region=Region.INDIA,
                title="Indian AI startup launches Hinglish coding assistant",
                description="A new developer tool is gaining attention in India.",
                channel_id="india-tech-one",
                channel_title="India Tech One",
                published_at=observed_at - timedelta(hours=4),
                observed_at=observed_at,
                view_count=950_000,
                like_count=61_000,
                comment_count=7_100,
                duration_seconds=312,
                category_id="28",
                tags=["AI", "India", "Hinglish"],
                source_url="https://www.youtube.com/watch?v=in-ai-1",
            ),
            TrendVideo(
                video_id="in-ai-2",
                region=Region.INDIA,
                title="Hinglish AI coding assistant becomes India's new tech trend",
                description="Developers react to the new assistant.",
                channel_id="bharat-builds",
                channel_title="Bharat Builds",
                published_at=observed_at - timedelta(hours=7),
                observed_at=observed_at,
                view_count=610_000,
                like_count=38_000,
                comment_count=4_400,
                duration_seconds=405,
                category_id="28",
                tags=["coding", "AI", "India"],
                source_url="https://www.youtube.com/watch?v=in-ai-2",
            ),
            TrendVideo(
                video_id="in-upi-1",
                region=Region.INDIA,
                title="UPI payment changes arrive for small businesses",
                description="Merchants explain what the new payment changes mean.",
                channel_id="money-india",
                channel_title="Money India",
                published_at=observed_at - timedelta(hours=12),
                observed_at=observed_at,
                view_count=480_000,
                like_count=21_000,
                comment_count=2_900,
                duration_seconds=521,
                category_id="25",
                tags=["UPI", "payments", "business"],
                source_url="https://www.youtube.com/watch?v=in-upi-1",
            ),
            TrendVideo(
                video_id="in-upi-2",
                region=Region.INDIA,
                title="Small businesses react to new UPI payment changes",
                description="A second perspective on the payment update.",
                channel_id="founders-desk",
                channel_title="Founders Desk",
                published_at=observed_at - timedelta(hours=10),
                observed_at=observed_at,
                view_count=330_000,
                like_count=18_000,
                comment_count=1_700,
                duration_seconds=367,
                category_id="25",
                tags=["UPI", "small business", "India"],
                source_url="https://www.youtube.com/watch?v=in-upi-2",
            ),
        ]

    @staticmethod
    def _us(observed_at):
        return [
            TrendVideo(
                video_id="us-agent-1",
                region=Region.UNITED_STATES,
                title="New AI agent changes how software teams review code",
                description="A new agent workflow is spreading across developer teams.",
                channel_id="future-stack",
                channel_title="Future Stack",
                published_at=observed_at - timedelta(hours=3),
                observed_at=observed_at,
                view_count=1_200_000,
                like_count=72_000,
                comment_count=8_200,
                duration_seconds=445,
                category_id="28",
                tags=["AI agents", "software", "code review"],
                source_url="https://www.youtube.com/watch?v=us-agent-1",
            ),
            TrendVideo(
                video_id="us-agent-2",
                region=Region.UNITED_STATES,
                title="Software teams test the new AI code review agent",
                description="Independent developers test the workflow.",
                channel_id="builder-report",
                channel_title="Builder Report",
                published_at=observed_at - timedelta(hours=5),
                observed_at=observed_at,
                view_count=830_000,
                like_count=49_000,
                comment_count=5_600,
                duration_seconds=381,
                category_id="28",
                tags=["AI", "agent", "code review"],
                source_url="https://www.youtube.com/watch?v=us-agent-2",
            ),
            TrendVideo(
                video_id="us-media-1",
                region=Region.UNITED_STATES,
                title="Streaming subscriptions reshape independent media business",
                description="A look at the latest creator business shift.",
                channel_id="culture-ledger",
                channel_title="Culture Ledger",
                published_at=observed_at - timedelta(hours=14),
                observed_at=observed_at,
                view_count=570_000,
                like_count=31_000,
                comment_count=3_200,
                duration_seconds=611,
                category_id="24",
                tags=["streaming", "media", "business"],
                source_url="https://www.youtube.com/watch?v=us-media-1",
            ),
            TrendVideo(
                video_id="us-media-2",
                region=Region.UNITED_STATES,
                title="Independent media business reacts to streaming subscriptions",
                description="Creators discuss subscription fatigue.",
                channel_id="creator-economy",
                channel_title="Creator Economy",
                published_at=observed_at - timedelta(hours=11),
                observed_at=observed_at,
                view_count=390_000,
                like_count=20_000,
                comment_count=2_200,
                duration_seconds=492,
                category_id="24",
                tags=["streaming", "subscriptions", "media"],
                source_url="https://www.youtube.com/watch?v=us-media-2",
            ),
        ]
