from editorial_shorts_agent.domain import (
    AcquisitionStatus,
    ClipPurpose,
    ClipRisk,
    EditorialClipCandidate,
    SourceReference,
)


def test_editorial_clip_preserves_source_and_exact_duration() -> None:
    clip = EditorialClipCandidate(
        source=SourceReference(
            source_url="https://example.com/source",
            creator="Example Publisher",
            source_title="Example source video",
            source_timestamp_seconds=44.0,
        ),
        start_seconds=44.0,
        end_seconds=45.75,
        narration_beat_id="beat-3",
        purpose=ClipPurpose.EDITORIAL_EXCERPT,
        risk=ClipRisk.HIGH,
        acquisition_status=AcquisitionStatus.REVIEW_REQUIRED,
        relevance_reason="The source directly shows the subject being discussed.",
    )

    assert clip.duration_seconds == 1.75
    assert clip.source.creator == "Example Publisher"
    assert clip.acquisition_status is AcquisitionStatus.REVIEW_REQUIRED
