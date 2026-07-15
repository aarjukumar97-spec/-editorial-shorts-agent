import httpx

from editorial_shorts_agent.domain import Region
from editorial_shorts_agent.providers.youtube import (
    YouTubeTrendProvider,
    parse_iso8601_duration,
)


def test_iso8601_duration_parser() -> None:
    assert parse_iso8601_duration("PT1M2S") == 62
    assert parse_iso8601_duration("PT2H3M4S") == 7_384
    assert parse_iso8601_duration("not-a-duration") == 0


async def test_provider_requests_regional_chart_and_parses_video() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["chart"] == "mostPopular"
        assert request.url.params["regionCode"] == "IN"
        assert request.url.params["maxResults"] == "10"
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "video-1",
                        "snippet": {
                            "title": "India AI story",
                            "description": "Description",
                            "channelId": "channel-1",
                            "channelTitle": "Channel One",
                            "publishedAt": "2026-07-14T12:00:00Z",
                            "categoryId": "28",
                            "tags": ["AI", "India"],
                        },
                        "statistics": {
                            "viewCount": "1234",
                            "likeCount": "100",
                            "commentCount": "20",
                        },
                        "contentDetails": {"duration": "PT1M2S"},
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = YouTubeTrendProvider(api_key="test-key", client=client)

    videos = await provider.fetch_most_popular(Region.INDIA, 10)
    await client.aclose()

    assert len(videos) == 1
    assert videos[0].region is Region.INDIA
    assert videos[0].duration_seconds == 62
    assert videos[0].view_count == 1234
    assert videos[0].source_url.endswith("video-1")
