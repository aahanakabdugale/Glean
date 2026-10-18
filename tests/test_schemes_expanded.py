"""
Tests for Scheme Expansion & Multi-Jurisdiction Catalog:
- India (8 schemes): PMJJBY, PMSBY, SSY, PM-KISAN, IGNOAPS, Ayushman, APY, SCSS
- USA (4 schemes): Medicare, Social Security, SNAP, 401(k) Catch-Up
"""

from datetime import date
import pytest

from backend.schemes import check_eligibility, load_schemes
from backend.tools import get_scheme_checklist

TODAY = date(2026, 10, 6)


def by_id(results, scheme_id):
    return next(r for r in results if r["scheme_id"] == scheme_id)


def test_catalog_has_eight_schemes():
    """Verify Indian catalog has 8 schemes and full catalog has 12 schemes."""
    in_schemes = load_schemes(country="IN")
    assert len(in_schemes) == 8
    in_ids = {s["id"] for s in in_schemes}
    expected_in = {
        "ignoaps_mh",
        "ayushman_vay_vandana",
        "apy",
        "scss",
        "pmjjby",
        "pmsby",
        "ssy",
        "pm_kisan",
    }
    assert in_ids == expected_in

    us_schemes = load_schemes(country="US")
    assert len(us_schemes) == 4
    us_ids = {s["id"] for s in us_schemes}
    expected_us = {
        "us_medicare",
        "us_social_security",
        "us_snap",
        "us_catchup_401k",
    }
    assert us_ids == expected_us

    all_schemes = load_schemes()
    assert len(all_schemes) == 12


def test_every_scheme_has_https_source_and_documents():
    for s in load_schemes():
        assert s["source_url"].startswith("https://")
        assert s["apply_url"].startswith("https://")
        assert len(s["documents"]) >= 2
        assert s["summary"]
        assert s["state"]
        assert s["country"] in ("IN", "US")


class TestPMJJBY:
    def test_adult_with_bank_account_eligible(self):
        # Age 30 (born 1996 in 2026)
        res = check_eligibility(1996, {"bank_account"}, TODAY)
        r = by_id(res, "pmjjby")
        assert r["status"] == "may_be_eligible"

    def test_adult_without_bank_account_check_needed(self):
        res = check_eligibility(1996, set(), TODAY)
        r = by_id(res, "pmjjby")
        assert r["status"] == "check_needed"
        assert "needs: bank_account" in r["confirm"]

    def test_age_over_50_not_eligible(self):
        # Age 52 (born 1974 in 2026)
        res = check_eligibility(1974, {"bank_account"}, TODAY)
        r = by_id(res, "pmjjby")
        assert r["status"] == "not_eligible"

    def test_age_16_almost_eligible(self):
        # Age 16 (born 2010 in 2026, min_age 18, gap 2)
        res = check_eligibility(2010, {"bank_account"}, TODAY)
        r = by_id(res, "pmjjby")
        assert r["status"] == "almost_eligible"
        assert r["years_until_eligible"] == 2
        assert r["eligible_from_year"] == 2028


class TestPMSBY:
    def test_working_parent_eligible(self):
        # Riley (born 1972, age 54 in 2026)
        res = check_eligibility(1972, {"bank_account"}, TODAY)
        r = by_id(res, "pmsby")
        assert r["status"] == "may_be_eligible"

    def test_senior_up_to_70_eligible(self):
        # Age 68 (born 1958 in 2026)
        res = check_eligibility(1958, {"bank_account"}, TODAY)
        r = by_id(res, "pmsby")
        assert r["status"] == "may_be_eligible"

    def test_over_70_not_eligible(self):
        # Chandler (born 1950, age 76 in 2026)
        res = check_eligibility(1950, {"bank_account"}, TODAY)
        r = by_id(res, "pmsby")
        assert r["status"] == "not_eligible"


class TestSSY:
    def test_girl_child_under_10_eligible(self):
        # Age 6 (born 2020 in 2026)
        res = check_eligibility(2020, {"girl_child"}, TODAY)
        r = by_id(res, "ssy")
        assert r["status"] == "may_be_eligible"

    def test_under_10_without_tag_check_needed(self):
        res = check_eligibility(2020, set(), TODAY)
        r = by_id(res, "ssy")
        assert r["status"] == "check_needed"
        assert "needs: girl_child" in r["confirm"]

    def test_child_over_10_not_eligible(self):
        # Age 12 (born 2014 in 2026)
        res = check_eligibility(2014, {"girl_child"}, TODAY)
        r = by_id(res, "ssy")
        assert r["status"] == "not_eligible"


class TestPMKisan:
    def test_farmer_eligible(self):
        # Age 40 with farmer tag
        res = check_eligibility(1986, {"farmer"}, TODAY)
        r = by_id(res, "pm_kisan")
        assert r["status"] == "may_be_eligible"

    def test_farmer_with_income_tax_excluded(self):
        res = check_eligibility(1986, {"farmer", "income_tax_payer"}, TODAY)
        r = by_id(res, "pm_kisan")
        assert r["status"] == "not_eligible"

    def test_unconfirmed_farmer_check_needed(self):
        res = check_eligibility(1986, set(), TODAY)
        r = by_id(res, "pm_kisan")
        assert r["status"] == "check_needed"


class TestUSMedicare:
    def test_senior_65_plus_eligible(self):
        # Chandler (born 1950, age 76 in 2026)
        res = check_eligibility(1950, set(), TODAY, country="US")
        r = by_id(res, "us_medicare")
        assert r["status"] == "may_be_eligible"

    def test_age_63_almost_eligible(self):
        # Age 63 (born 1963 in 2026, min_age 65, gap 2 years)
        res = check_eligibility(1963, set(), TODAY, country="US")
        r = by_id(res, "us_medicare")
        assert r["status"] == "almost_eligible"
        assert r["years_until_eligible"] == 2
        assert r["eligible_from_year"] == 2028

    def test_under_62_not_eligible(self):
        # Justin (born 1968, age 58 in 2026, gap 7 years > 3)
        res = check_eligibility(1968, set(), TODAY, country="US")
        r = by_id(res, "us_medicare")
        assert r["status"] == "not_eligible"


class TestUSSocialSecurity:
    def test_senior_62_plus_eligible(self):
        # Age 65 (born 1961 in 2026)
        res = check_eligibility(1961, set(), TODAY, country="US")
        r = by_id(res, "us_social_security")
        assert r["status"] == "may_be_eligible"

    def test_age_60_almost_eligible(self):
        # Age 60 (born 1966 in 2026, min_age 62, gap 2 years)
        res = check_eligibility(1966, set(), TODAY, country="US")
        r = by_id(res, "us_social_security")
        assert r["status"] == "almost_eligible"
        assert r["years_until_eligible"] == 2
        assert r["eligible_from_year"] == 2028


class TestUSSNAP:
    def test_with_low_income_eligible(self):
        res = check_eligibility(1990, {"low_income"}, TODAY, country="US")
        r = by_id(res, "us_snap")
        assert r["status"] == "may_be_eligible"

    def test_without_tag_check_needed(self):
        res = check_eligibility(1990, set(), TODAY, country="US")
        r = by_id(res, "us_snap")
        assert r["status"] == "check_needed"
        assert "needs: low_income" in r["confirm"]


class TestUSCatchup401k:
    def test_age_50_plus_employed_eligible(self):
        # Justin (born 1968, age 58 in 2026)
        res = check_eligibility(1968, {"employed"}, TODAY, country="US")
        r = by_id(res, "us_catchup_401k")
        assert r["status"] == "may_be_eligible"

    def test_under_50_not_eligible(self):
        # Jace (born 2000, age 26 in 2026)
        res = check_eligibility(2000, {"employed"}, TODAY, country="US")
        r = by_id(res, "us_catchup_401k")
        assert r["status"] == "not_eligible"


def test_get_scheme_checklist_new_schemes():
    checklist_pmjjby = get_scheme_checklist("pmjjby")
    assert "Jeevan Jyoti" in checklist_pmjjby
    assert "Aadhaar card" in checklist_pmjjby

    checklist_ssy = get_scheme_checklist("ssy")
    assert "Sukanya Samriddhi" in checklist_ssy
    assert "Birth certificate of the girl child" in checklist_ssy

    checklist_kisan = get_scheme_checklist("pm_kisan")
    assert "PM Kisan" in checklist_kisan
    assert "Khasra/Khatauni" in checklist_kisan

    checklist_medicare = get_scheme_checklist("us_medicare")
    assert "Medicare" in checklist_medicare
    assert "CMS-40B" in checklist_medicare

    checklist_ssa = get_scheme_checklist("us_social_security")
    assert "Social Security" in checklist_ssa
    assert "Birth Certificate" in checklist_ssa
