from datetime import date
import sqlite3
import pytest

import backend.db as glean_db
from backend.schemes import (
    ALMOST_ELIGIBLE_WINDOW_YEARS,
    check_eligibility,
    load_schemes,
)
from backend.tools import check_scheme_eligibility

TODAY = date(2026, 10, 6)


def by_id(results, scheme_id):
    return next(r for r in results if r["scheme_id"] == scheme_id)


# ---------------------------------------------------------------------------
# Fixture for tool tests
# ---------------------------------------------------------------------------

@pytest.fixture
def db_conn(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    glean_db.init_db(conn)
    monkeypatch.setattr(glean_db, "get_connection", lambda *args, **kwargs: conn)
    yield conn


# ---------------------------------------------------------------------------
# Core almost_eligible tests
# ---------------------------------------------------------------------------

class TestAlmostEligibleCore:
    def test_window_constant(self):
        assert ALMOST_ELIGIBLE_WINDOW_YEARS == 3

    def test_exactly_1_year_away_is_almost(self):
        # 2026 - 1967 = age 59. SCSS min_age = 60. Gap = 1 year.
        res = check_eligibility(1967, set(), TODAY)
        assert by_id(res, "scss")["status"] == "almost_eligible"

    def test_exactly_3_years_away_is_almost(self):
        # 2026 - 1969 = age 57. SCSS min_age = 60. Gap = 3 years.
        res = check_eligibility(1969, set(), TODAY)
        assert by_id(res, "scss")["status"] == "almost_eligible"

    def test_exactly_4_years_away_is_not_eligible(self):
        # 2026 - 1970 = age 56. SCSS min_age = 60. Gap = 4 years (outside window).
        res = check_eligibility(1970, set(), TODAY)
        assert by_id(res, "scss")["status"] == "not_eligible"

    def test_at_min_age_is_eligible_not_almost(self):
        # 2026 - 1966 = age 60. SCSS min_age = 60.
        res = check_eligibility(1966, set(), TODAY)
        assert by_id(res, "scss")["status"] == "may_be_eligible"

    def test_above_min_age_is_eligible_not_almost(self):
        # 2026 - 1960 = age 66. SCSS min_age = 60.
        res = check_eligibility(1960, set(), TODAY)
        assert by_id(res, "scss")["status"] == "may_be_eligible"

    def test_almost_eligible_fields_present(self):
        res = check_eligibility(1969, set(), TODAY, member_name="Justin")
        r = by_id(res, "scss")
        assert r["status"] == "almost_eligible"
        assert "years_until_eligible" in r
        assert "eligible_from_year" in r
        assert "spoken_hint" in r
        assert "suggested_task" in r

    def test_years_until_and_from_year_values(self):
        res = check_eligibility(1969, set(), TODAY, member_name="Justin")
        r = by_id(res, "scss")
        assert r["years_until_eligible"] == 3
        assert r["eligible_from_year"] == 2029

    def test_max_age_failure_never_almost(self):
        # APY min_age=18, max_age=40. 2026 - 1985 = age 41 (over max_age).
        res = check_eligibility(1985, set(), TODAY)
        assert by_id(res, "apy")["status"] == "not_eligible"

    def test_excludes_tag_blocks_almost(self):
        # APY min_age=18. 2026 - 2010 = age 16 (gap = 2).
        # But has income_tax_payer tag (excluded).
        res = check_eligibility(2010, {"income_tax_payer"}, TODAY)
        assert by_id(res, "apy")["status"] == "not_eligible"

    def test_unconfirmed_requires_gives_check_needed_not_almost(self):
        # IGNOAPS_MH min_age=65, requires=["bpl"]. 2026 - 1963 = age 63 (gap = 2).
        # But bpl is missing/unconfirmed.
        res = check_eligibility(1963, set(), TODAY)
        assert by_id(res, "ignoaps_mh")["status"] == "check_needed"

    def test_future_birth_year_not_eligible(self):
        res = check_eligibility(2030, set(), TODAY)
        for r in res:
            assert r["status"] in ("not_eligible", "check_needed")

    def test_non_almost_result_has_no_extra_fields(self):
        res = check_eligibility(1966, set(), TODAY)
        r = by_id(res, "scss")
        assert r["status"] == "may_be_eligible"
        assert "years_until_eligible" not in r
        assert "eligible_from_year" not in r
        assert "spoken_hint" not in r
        assert "suggested_task" not in r

    def test_ordering_eligible_before_almost(self):
        # Age 62 (birth_year 1964):
        # SCSS (min_age 60): 62 >= 60 -> may_be_eligible
        # IGNOAPS_MH (min_age 65) with bpl: 65 - 62 = 3 -> almost_eligible
        res = check_eligibility(1964, {"bpl"}, TODAY)
        scss = by_id(res, "scss")
        pension = by_id(res, "ignoaps_mh")
        assert scss["status"] == "may_be_eligible"
        assert pension["status"] == "almost_eligible"


# ---------------------------------------------------------------------------
# Spoken hint tests
# ---------------------------------------------------------------------------

class TestSpokenHint:
    def test_spoken_hint_with_name(self):
        res = check_eligibility(1969, set(), TODAY, member_name="Justin")
        r = by_id(res, "scss")
        assert "Justin" in r["spoken_hint"]
        assert "2029" in r["spoken_hint"]

    def test_spoken_hint_without_name(self):
        res = check_eligibility(1969, set(), TODAY, member_name="")
        r = by_id(res, "scss")
        assert "may qualify around 2029" in r["spoken_hint"]
        assert not r["spoken_hint"].startswith("Justin")


# ---------------------------------------------------------------------------
# Suggested task tests
# ---------------------------------------------------------------------------

class TestSuggestedTask:
    def test_suggested_task_shape(self):
        res = check_eligibility(1969, set(), TODAY, member_name="Justin")
        r = by_id(res, "scss")
        task = r["suggested_task"]
        assert isinstance(task, dict)
        assert isinstance(task["title"], str)
        assert isinstance(task["due_year"], int)

    def test_suggested_task_due_year_matches_eligible_from_year(self):
        res = check_eligibility(1969, set(), TODAY, member_name="Justin")
        r = by_id(res, "scss")
        assert r["suggested_task"]["due_year"] == r["eligible_from_year"] == 2029


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    def test_existing_result_keys_unchanged(self):
        results = check_eligibility(1970, set(), TODAY)
        expected = {"scheme_id", "name", "status", "reasons", "confirm", "source_url"}
        for r in results:
            assert expected.issubset(r.keys())

    def test_original_statuses_still_valid(self):
        # 1950, age 76 with bpl: ignoaps_mh=may_be_eligible, ayushman=may_be_eligible, scss=may_be_eligible, apy=not_eligible
        res = check_eligibility(1950, {"bpl"}, TODAY)
        for r in res:
            assert r["status"] != "almost_eligible"


# ---------------------------------------------------------------------------
# Tool-level tests for check_scheme_eligibility
# ---------------------------------------------------------------------------

class TestCheckSchemeEligibilityTool:
    def test_tool_includes_almost_eligible_section(self, db_conn):
        db_conn.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            ("Justin", "Father", 1969, "healthy"),
        )
        db_conn.commit()

        output = check_scheme_eligibility("Justin")
        assert "Coming up soon:" in output
        assert "Senior Citizens Savings Scheme" in output
        assert "may qualify around 2029" in output
        assert "Suggested: Check eligibility for Senior Citizens Savings Scheme (around 2029)" in output

    def test_tool_ordering_eligible_before_almost(self, db_conn):
        # Born 1964 with bpl: SCSS is eligible (age 62 >= 60), IGNOAPS_MH is almost (65 - 62 = 3)
        db_conn.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            ("Suresh", "Father", 1964, "healthy"),
        )
        db_conn.commit()

        output = check_scheme_eligibility("Suresh", tags="bpl")
        assert "May be eligible:" in output
        assert "Coming up soon:" in output
        pos_eligible = output.index("May be eligible:")
        pos_almost = output.index("Coming up soon:")
        assert pos_eligible < pos_almost

    def test_tool_no_almost_section_when_not_applicable(self, db_conn):
        db_conn.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            ("Ramesh", "Grandfather", 1950, "healthy"),
        )
        db_conn.commit()

        output = check_scheme_eligibility("Ramesh")
        assert "Coming up soon:" not in output

    def test_tool_disclaimer_still_present(self, db_conn):
        db_conn.execute(
            "INSERT INTO family_members (name, relation, birth_year, status) VALUES (?, ?, ?, ?)",
            ("Justin", "Father", 1969, "healthy"),
        )
        db_conn.commit()

        output = check_scheme_eligibility("Justin")
        assert "Note: Guidance only. Please verify details on official government portals." in output
