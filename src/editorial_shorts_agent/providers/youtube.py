from __future__ import annotations

import re
from typing import Any

import httpx

from editorial_shorts_agent.domain import Region, TrendVideo, utc_now


_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?)?$"
)


class TrendProviderError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def parse_iso8601_duration(value: str) -> int:
    match = _DURATION.fullmatch(value)
    if not match:
        return 0
    parts = {name: int(amount or 0) for name, amount in match.groupdict().items()}
    return (
        (parts["days"] * 86_400)
        + (parts["hours"] * 3_600)
        + (parts["minutes"] * 60)
        + parts["seconds"]
    )


class YouTubeTrendProvider:
    endpoint = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("A YouTube API key is required for the youtube trend provider")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._client = client

    @property
    def name(self) -> str:
        return "youtube"

    async def fetch_most_popular(self, region: Region, max_results: int) -> list[TrendVideo]:
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region.value,
            "maxResults": min(max(max_results, 1), 50),
            "key": self._api_key,
            "fields": (
                "items(id,snippet(title,description,channelId,channelTitle,publishedAt,"
                "categoryId,tags),statistics(viewCount,likeCount,commentCount),"
                "contentDetails(duration))"
            ),
        }
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout_seconds)
        try:
            response = await client.get(self.endpoint, params=params)
            response.raise_for_status()
            body = response.json()
        except httpx.TimeoutException as exc:
            raise TrendProviderError(
                "YOUTUBE_TIMEOUT",
                "YouTube did not respond before the configured timeout.",
                retryable=True,
            ) from exc
        except httpx.HTTPStatusError as exc:
            retryable = exc.response.status_code >= 500 or exc.response.status_code == 429
            raise TrendProviderError(
                "YOUTUBE_HTTP_ERROR",
                f"YouTube returned HTTP {exc.response.status_code}.",
                retryable=retryable,
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise TrendProviderError(
                "YOUTUBE_RESPONSE_ERROR",
                "YouTube returned an unreadable response.",
                retryable=True,
            ) from exc
        finally:
            if owns_client:
                await client.aclose()

        observed_at = utc_now()
        return [self._parse_item(item, region, observed_at) for item in body.get("items", [])]

    @staticmethod
    def _parse_item(item: dict[str, Any], region: Region, observed_at) -> TrendVideo:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        details = item.get("contentDetails", {})
        video_id = str(item.get("id", ""))
        return TrendVideo(
            video_id=video_id,
            region=region,
            title=str(snippet.get("title", "Untitled video")),
            description=str(snippet.get("description", "")),
            channel_id=str(snippet.get("channelId", "unknown-channel")),
            channel_title=str(snippet.get("channelTitle", "Unknown channel")),
            published_at=snippet.get("publishedAt", observed_at),
            observed_at=observed_at,
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            duration_seconds=parse_iso8601_duration(str(details.get("duration", ""))),
            category_id=snippet.get("categoryId"),
            tags=[str(tag) for tag in snippet.get("tags", [])],
            source_url=f"https://www.youtube.com/watch?v={video_id}",
        )
