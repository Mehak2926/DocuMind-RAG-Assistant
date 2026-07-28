def filter_by_threshold(scores: list[float], threshold: float) -> list[float]:
    return [score for score in scores if score >= threshold]


def test_relevance_threshold_removes_weak_matches() -> None:
    assert filter_by_threshold([0.82, 0.36, 0.19], 0.35) == [0.82, 0.36]
