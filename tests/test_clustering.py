from editorial_shorts_agent.clustering import LexicalTopicClusterer
from tests.factories import trend_video


def test_related_titles_form_one_topic_and_unrelated_title_stays_separate() -> None:
    videos = [
        trend_video(
            video_id="ai-1",
            title="Indian AI startup launches Hinglish coding assistant",
            channel_id="one",
            views=500_000,
        ),
        trend_video(
            video_id="ai-2",
            title="Hinglish AI coding assistant becomes major India trend",
            channel_id="two",
            views=350_000,
        ),
        trend_video(
            video_id="upi-1",
            title="UPI payment rules change for merchants",
            channel_id="three",
            views=200_000,
        ),
    ]

    topics = LexicalTopicClusterer().cluster(videos)

    assert len(topics) == 2
    grouped_ids = [{video.video_id for video in topic.videos} for topic in topics]
    assert {"ai-1", "ai-2"} in grouped_ids
    assert {"upi-1"} in grouped_ids


def test_cluster_identity_is_deterministic() -> None:
    videos = [
        trend_video(
            video_id="one",
            title="AI agent changes software code review",
            channel_id="a",
        ),
        trend_video(
            video_id="two",
            title="Software teams test AI code review agent",
            channel_id="b",
        ),
    ]
    clusterer = LexicalTopicClusterer()

    first = clusterer.cluster(videos)[0]
    second = clusterer.cluster(list(reversed(videos)))[0]

    assert first.topic_id == second.topic_id
