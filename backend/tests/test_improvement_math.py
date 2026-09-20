"""The awareness-improvement formula, including the case that breaks it.

The project's headline metric is ((post - pre) / pre) * 100. These tests pin down what the
system does when pre == 0, because that is a real occurrence with first-time internet users
and a naive implementation either crashes or prints infinity.
"""

from __future__ import annotations

import pytest

from app.services.assessment_service import compute_improvement, paired_t_test


class _FakeAssessment:
    def __init__(self, score: int, max_score: int = 10):
        self.score = score
        self.max_score = max_score


def improvement(pre: int | None, post: int | None, max_score: int = 10) -> dict:
    return compute_improvement(
        _FakeAssessment(pre, max_score) if pre is not None else None,
        _FakeAssessment(post, max_score) if post is not None else None,
    )


class TestImprovementFormula:
    def test_standard_case_matches_the_formula(self):
        # ((8 - 4) / 4) * 100 = 100.0
        assert improvement(4, 8)["improvement_percentage"] == 100.0

    def test_another_standard_case(self):
        # ((7 - 5) / 5) * 100 = 40.0
        assert improvement(5, 7)["improvement_percentage"] == 40.0

    def test_no_change_is_zero_percent(self):
        assert improvement(6, 6)["improvement_percentage"] == 0.0

    def test_decline_is_negative(self):
        assert improvement(8, 4)["improvement_percentage"] == -50.0

    def test_percentages_are_computed(self):
        result = improvement(4, 8)
        assert result["pre_percentage"] == 40.0
        assert result["post_percentage"] == 80.0


class TestZeroPreScoreGuard:
    """The division-by-zero case — the whole reason the guard exists."""

    def test_no_crash_when_pre_is_zero(self):
        result = improvement(0, 5)  # must not raise ZeroDivisionError
        assert result is not None

    def test_percentage_is_none_not_infinity(self):
        result = improvement(0, 5)
        assert result["improvement_percentage"] is None

    def test_absolute_gain_is_reported_instead(self):
        assert improvement(0, 5)["absolute_gain"] == 5

    def test_normalized_gain_is_reported_instead(self):
        # Hake's normalized gain: (post - pre) / (max - pre) = (5 - 0) / (10 - 0) = 0.5
        assert improvement(0, 5)["normalized_gain"] == 0.5

    def test_explanatory_note_is_present(self):
        note = improvement(0, 5)["note"]
        assert note is not None
        assert "undefined" in note.lower()

    def test_no_note_for_normal_case(self):
        assert improvement(4, 8)["note"] is None

    def test_zero_to_zero_is_handled(self):
        result = improvement(0, 0)
        assert result["improvement_percentage"] is None
        assert result["absolute_gain"] == 0

    def test_perfect_pre_score_normalized_gain(self):
        # max - pre == 0; no headroom to improve, and post is also perfect
        result = improvement(10, 10)
        assert result["normalized_gain"] == 1.0
        assert result["improvement_percentage"] == 0.0


class TestIncompleteData:
    def test_missing_post_test(self):
        result = improvement(5, None)
        assert result["post_score"] is None
        assert result["improvement_percentage"] is None
        assert result["band"] == "post-test pending"

    def test_missing_pre_test(self):
        result = improvement(None, 7)
        assert result["pre_score"] is None
        assert result["improvement_percentage"] is None


class TestBands:
    def test_aware_band(self):
        assert improvement(4, 8)["band"] == "aware"

    def test_partially_aware_band(self):
        assert improvement(3, 6)["band"] == "partially aware"

    def test_needs_followup_band(self):
        assert improvement(2, 4)["band"] == "needs follow-up"


class TestPairedTTest:
    def test_clear_improvement_is_significant(self):
        # Gains vary between participants, as real cohort data does.
        pre = [3, 4, 2, 5, 3, 4, 2, 3, 4, 3]
        post = [7, 9, 5, 8, 6, 9, 7, 6, 8, 5]
        result = paired_t_test(pre, post)
        assert result["t_statistic"] > 0
        assert result["p_value"] < 0.05
        assert result["cohens_d"] > 0.8  # large effect

    def test_no_change_is_handled(self):
        scores = [5, 5, 5, 5]
        result = paired_t_test(scores, scores)
        assert result["t_statistic"] is None  # zero variance, undefined

    def test_identical_gains_are_undefined_not_crashed(self):
        """Every participant gaining exactly the same amount gives zero variance.

        The t-statistic divides by the standard deviation of the differences, so this is
        undefined rather than infinitely significant. It must return None, not raise.
        """
        pre = [3, 4, 2, 5]
        post = [7, 8, 6, 9]  # every difference is exactly +4
        result = paired_t_test(pre, post)
        assert result["t_statistic"] is None
        assert "note" in result

    def test_too_few_pairs(self):
        result = paired_t_test([4], [8])
        assert result["t_statistic"] is None
        assert result["n"] == 1

    def test_decline_gives_negative_t(self):
        pre = [8, 9, 7, 8, 9]
        post = [4, 6, 3, 5, 4]
        assert paired_t_test(pre, post)["t_statistic"] < 0


@pytest.mark.parametrize(
    "pre,post,expected",
    [
        (1, 10, 900.0),   # small denominator inflates the ratio enormously
        (2, 4, 100.0),
        (5, 10, 100.0),
        (9, 10, 11.11),
    ],
)
def test_ratio_sensitivity_to_low_denominator(pre, post, expected):
    """Documents why the mean improvement % is skewed and the median should be quoted."""
    assert improvement(pre, post)["improvement_percentage"] == expected
