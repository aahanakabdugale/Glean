"""Extra tests for glean.schemes — boundary ages, edge-case tags, and result shape.

TODAY is fixed to 2026-10-06 (same convention as test_schemes.py).
age = 2026 - birth_year  (birth-year-only arithmetic used in schemes.py)

Boundary mapping
-----------------
age 64  → birth_year 1962   age 65  → birth_year 1961   (ignoaps_mh min_age=65)
age 69  → birth_year 1957   age 70  → birth_year 1956   (ayushman_vay_vandana min_age=70)
age 17  → birth_year 2009   age 18  → birth_year 2008   (apy min_age=18)
age 40  → birth_year 1986   age 41  → birth_year 1985   (apy max_age=40)
age 59  → birth_year 1967   age 60  → birth_year 1966   (scss min_age=60)
"""

from datetime import date

import pytest

from glean.schemes import check_eligibility

TODAY = date(2026, 10, 6)

EXPECTED_KEYS = {"scheme_id", "name", "status", "reasons", "confirm", "source_url"}
VALID_STATUSES = {"may_be_eligible", "check_needed", "not_eligible"}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def by_id(results, scheme_id):
    return next(r for r in results if r["scheme_id"] == scheme_id)


# ---------------------------------------------------------------------------
# Result shape: every item must have the six required keys
# ---------------------------------------------------------------------------

class TestResultShape:
    def test_all_results_have_required_keys(self):
        results = check_eligibility(1970, set(), TODAY)
        assert results, "check_eligibility returned an empty list"
        for r in results:
            missing = EXPECTED_KEYS - r.keys()
            assert not missing, f"scheme {r.get('scheme_id')} missing keys: {missing}"

    def test_status_is_always_valid(self):
        results = check_eligibility(1970, set(), TODAY)
        for r in results:
            assert r["status"] in VALID_STATUSES, (
                f"scheme {r['scheme_id']} has unexpected status {r['status']!r}"
            )

    def test_reasons_and_confirm_are_lists(self):
        results = check_eligibility(1970, set(), TODAY)
        for r in results:
            assert isinstance(r["reasons"], list), f"{r['scheme_id']}.reasons is not a list"
            assert isinstance(r["confirm"], list), f"{r['scheme_id']}.confirm is not a list"


# ---------------------------------------------------------------------------
# Boundary ages: ignoaps_mh  (min_age = 65)
# ---------------------------------------------------------------------------

class TestBoundaryIgnoaps:
    def test_age_64_not_eligible(self):
        """Just below the threshold — must be not_eligible."""
        res = check_eligibility(1962, {"bpl"}, TODAY)
        assert by_id(res, "ignoaps_mh")["status"] == "not_eligible"

    def test_age_65_may_be_eligible(self):
        """Exactly at the threshold with bpl — may_be_eligible."""
        res = check_eligibility(1961, {"bpl"}, TODAY)
        assert by_id(res, "ignoaps_mh")["status"] == "may_be_eligible"

    def test_age_65_without_bpl_check_needed(self):
        """At threshold but bpl unknown — check_needed."""
        res = check_eligibility(1961, set(), TODAY)
        assert by_id(res, "ignoaps_mh")["status"] == "check_needed"


# ---------------------------------------------------------------------------
# Boundary ages: ayushman_vay_vandana  (min_age = 70)
# ---------------------------------------------------------------------------

class TestBoundaryAyushman:
    def test_age_69_not_eligible(self):
        res = check_eligibility(1957, set(), TODAY)
        assert by_id(res, "ayushman_vay_vandana")["status"] == "not_eligible"

    def test_age_70_may_be_eligible(self):
        res = check_eligibility(1956, set(), TODAY)
        assert by_id(res, "ayushman_vay_vandana")["status"] == "may_be_eligible"


# ---------------------------------------------------------------------------
# Boundary ages: apy  (min_age = 18, max_age = 40, excludes income_tax_payer)
# ---------------------------------------------------------------------------

class TestBoundaryApy:
    def test_age_17_not_eligible(self):
        res = check_eligibility(2009, set(), TODAY)
        assert by_id(res, "apy")["status"] == "not_eligible"

    def test_age_18_may_be_eligible_no_tags(self):
        """Exactly 18, no tags: age fits and nothing is required, so may_be_eligible."""
        res = check_eligibility(2008, set(), TODAY)
        assert by_id(res, "apy")["status"] == "may_be_eligible"
        
    def test_age_40_may_be_eligible(self):
        """Still within the upper bound."""
        res = check_eligibility(1986, set(), TODAY)
        assert by_id(res, "apy")["status"] == "may_be_eligible"

    def test_age_41_not_eligible(self):
        """One year past the max_age — not_eligible."""
        res = check_eligibility(1985, set(), TODAY)
        assert by_id(res, "apy")["status"] == "not_eligible"

    def test_age_40_income_tax_payer_not_eligible(self):
        """At the upper boundary but excluded by tag."""
        res = check_eligibility(1986, {"income_tax_payer"}, TODAY)
        assert by_id(res, "apy")["status"] == "not_eligible"


# ---------------------------------------------------------------------------
# Boundary ages: scss  (min_age = 60)
# ---------------------------------------------------------------------------

class TestBoundaryScss:
    def test_age_59_not_eligible(self):
        res = check_eligibility(1967, set(), TODAY)
        assert by_id(res, "scss")["status"] == "not_eligible"

    def test_age_60_may_be_eligible(self):
        res = check_eligibility(1966, set(), TODAY)
        assert by_id(res, "scss")["status"] == "may_be_eligible"


# ---------------------------------------------------------------------------
# Empty and unknown tags
# ---------------------------------------------------------------------------

class TestTagEdgeCases:
    def test_empty_tags_returns_results(self):
        """Passing no tags should not crash and should return results."""
        results = check_eligibility(1970, set(), TODAY)
        assert len(results) > 0

    def test_none_tags_returns_results(self):
        """Passing None for tags should be treated the same as an empty set."""
        results = check_eligibility(1970, None, TODAY)
        assert len(results) > 0

    def test_unknown_tag_ignored(self):
        """An unrecognised tag should not crash or alter eligibility."""
        results_no_tag = check_eligibility(1970, set(), TODAY)
        results_with_tag = check_eligibility(1970, {"completely_unknown_tag_xyz"}, TODAY)
        # Statuses must be identical for every scheme
        for r_no, r_with in zip(results_no_tag, results_with_tag):
            assert r_no["status"] == r_with["status"], (
                f"Unknown tag changed status for {r_no['scheme_id']}"
            )

    def test_multiple_unknown_tags_ignored(self):
        results = check_eligibility(1966, {"foo", "bar", "baz"}, TODAY)
        # scss: age 60, no known tags → may_be_eligible
        assert by_id(results, "scss")["status"] == "may_be_eligible"

    def test_not_eligible_confirm_is_empty(self):
        """When not_eligible, the confirm list must always be empty."""
        results = check_eligibility(2009, set(), TODAY)  # age 17, under apy min
        r = by_id(results, "apy")
        assert r["status"] == "not_eligible"
        assert r["confirm"] == []
