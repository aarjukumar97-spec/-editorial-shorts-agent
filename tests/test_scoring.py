from editorial_shorts_agent.clustering import LexicalTopicClusterer
from editorial_shorts_agent.domain import TrendStage
from editorial_shorts_agent.scoring import WeightedOpportunityScorer
from tests.factories import trend_video


def test_fresh_multi_channel_topic_ranks_above_old_single_source() -> None:
    videos = [
        trend_video(
            video_id="fresh-1",
            title="AI agent transforms software code review",
            channel_id="one",
            age_hours=2,
            views=700_000,
        ),
        trend_video(
            video_id="fresh-2",
            title="Software teams adopt AI code review agent",
            channel_id="two",
            age_hours=3,
            views=550_000,
        ),
        trend_video(
            video_id="old-1",
            title="Streaming subscription business documentary",
            channel_id="three",
            age_hours=160,
            views=80_000,
        ),
    ]
    seeds = LexicalTopicClusterer().cluster(videos)

    opportunities = WeightedOpportunityScorer().score(seeds)

    assert opportunities[0].rank == 1
    assert {video.video_id for video in opportunities[0].source_videos} == {
        "fresh-1",
        "fresh-2",
    }
    assert opportunities[0].stage in {
        TrendStage.EMERGING_CANDIDATE,
        TrendStage.SURGING_CANDIDATE,
    }
    assert opportunities[-1].stage is TrendStage.SINGLE_SOURCE
    assert opportunities[0].score.total > opportunities[-1].score.total


def test_score_components_are_bounded() -> None:
    seed = LexicalTopicClusterer().cluster(
        [
            trend_video(
                video_id="bounded",
                title="Technology culture story",
                channel_id="one",
                views=9_999_999_999,
            )
        ]
    )

    result = WeightedOpportunityScorer().score(seed)[0].score

    assert 0 <= result.total <= 100
    assert 0 <= result.estimated_view_velocity <= 1
    assert 0 <= result.freshness <= 1
