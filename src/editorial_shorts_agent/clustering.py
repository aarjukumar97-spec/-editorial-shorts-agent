from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, UUID, uuid5

from editorial_shorts_agent.domain import Region, TrendVideo


_TOKEN_PATTERN = re.compile(r"[^\w]+", flags=re.UNICODE)
_STOPWORDS = {
    "about",
    "after",
    "again",
    "breaking",
    "explained",
    "from",
    "gets",
    "have",
    "here",
    "into",
    "latest",
    "launch",
    "launches",
    "live",
    "more",
    "news",
    "official",
    "shorts",
    "that",
    "this",
    "today",
    "video",
    "what",
    "when",
    "where",
    "with",
    "your",
}


@dataclass(slots=True)
class TopicSeed:
    topic_id: UUID
    region: Region
    label: str
    keywords: list[str]
    videos: list[TrendVideo] = field(default_factory=list)


def title_tokens(video: TrendVideo) -> set[str]:
    normalized = unicodedata.normalize("NFKC", video.title).casefold()
    tokens = {
        token
        for token in _TOKEN_PATTERN.sub(" ", normalized).split()
        if token not in _STOPWORDS and (len(token) >= 3 or token in {"ai", "x"})
    }
    return tokens


def _similarity(left: set[str], right: set[str]) -> tuple[float, int]:
    if not left or not right:
        return 0.0, 0
    shared = left & right
    overlap = len(shared) / min(len(left), len(right))
    jaccard = len(shared) / len(left | right)
    return (0.65 * overlap) + (0.35 * jaccard), len(shared)


class LexicalTopicClusterer:
    """Deterministic baseline that can later be replaced by a multilingual model tool."""

    def __init__(self, similarity_threshold: float = 0.28) -> None:
        self._similarity_threshold = similarity_threshold

    def cluster(self, videos: list[TrendVideo]) -> list[TopicSeed]:
        if not videos:
            return []

        buckets: list[list[TrendVideo]] = []
        bucket_tokens: list[set[str]] = []

        for video in sorted(videos, key=lambda item: (-item.view_count, item.video_id)):
            tokens = title_tokens(video)
            best_index: int | None = None
            best_similarity = 0.0

            for index, existing_tokens in enumerate(bucket_tokens):
                similarity, shared_count = _similarity(tokens, existing_tokens)
                if shared_count >= 2 and similarity > best_similarity:
                    best_index = index
                    best_similarity = similarity

            if best_index is not None and best_similarity >= self._similarity_threshold:
                buckets[best_index].append(video)
                bucket_tokens[best_index].update(tokens)
            else:
                buckets.append([video])
                bucket_tokens.append(set(tokens))

        return [self._to_seed(bucket) for bucket in buckets]

    @staticmethod
    def _to_seed(videos: list[TrendVideo]) -> TopicSeed:
        token_counts: Counter[str] = Counter()
        for video in videos:
            token_counts.update(title_tokens(video))
        keywords = [token for token, _ in token_counts.most_common(6)]
        label = " ".join(keywords[:4]).title() or videos[0].title
        region = videos[0].region
        identity = f"{region.value}:{','.join(sorted(video.video_id for video in videos))}"
        return TopicSeed(
            topic_id=uuid5(NAMESPACE_URL, identity),
            region=region,
            label=label,
            keywords=keywords,
            videos=videos,
        )
