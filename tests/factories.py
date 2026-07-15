from datetime import timedelta

from editorial_shorts_agent.domain import Region, TrendVideo, utc_now


def trend_video(
    *,
    video_id: str,
    title: str,
    channel_id: str,
    region: Region = Region.INDIA,
    age_hours: int = 4,
    views: int = 100_000,
) -> TrendVideo:
    now = utc_now()
    return TrendVideo(
        video_id=video_id,
        region=region,
        title=title,
        description="Test source",
        channel_id=channel_id,
        channel_title=f"Channel {channel_id}",
        published_at=now - timedelta(hours=age_hours),
        observed_at=now,
        view_count=views,
        source_url=f"https://www.youtube.com/watch?v={video_id}",
    )
