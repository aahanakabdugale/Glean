from datetime import date

from glean.schemes import age_from_birth_year, check_eligibility, load_schemes

TODAY = date(2026, 10, 6)  # fixed so tests never break as years pass


def by_id(results, scheme_id):
    return next(r for r in results if r["scheme_id"] == scheme_id)


def test_age_from_birth_year():
    assert age_from_birth_year(1950, TODAY) == 76


def test_senior_with_bpl_may_be_eligible():
    res = check_eligibility(1950, {"bpl"}, TODAY)
    assert by_id(res, "ignoaps_mh")["status"] == "may_be_eligible"
    assert by_id(res, "ayushman_vay_vandana")["status"] == "may_be_eligible"
    assert by_id(res, "scss")["status"] == "may_be_eligible"


def test_senior_too_old_for_apy():
    res = check_eligibility(1950, {"bpl"}, TODAY)
    assert by_id(res, "apy")["status"] == "not_eligible"


def test_missing_bpl_needs_check():
    res = check_eligibility(1950, set(), TODAY)
    r = by_id(res, "ignoaps_mh")
    assert r["status"] == "check_needed"
    assert "needs: bpl" in r["confirm"]


def test_age_64_misses_pension_and_ayushman():
    res = check_eligibility(1962, {"bpl"}, TODAY)
    assert by_id(res, "ignoaps_mh")["status"] == "not_eligible"
    assert by_id(res, "ayushman_vay_vandana")["status"] == "not_eligible"
    assert by_id(res, "scss")["status"] == "may_be_eligible"


def test_young_adult_apy_depends_on_tax_status():
    res = check_eligibility(1996, set(), TODAY)
    assert by_id(res, "apy")["status"] == "may_be_eligible"
    res = check_eligibility(1996, {"income_tax_payer"}, TODAY)
    assert by_id(res, "apy")["status"] == "not_eligible"


def test_not_eligible_has_no_confirm_noise():
    res = check_eligibility(1950, set(), TODAY)
    assert by_id(res, "apy")["confirm"] == []


def test_every_scheme_has_official_source_and_documents():
    for s in load_schemes():
        assert s["source_url"].startswith("https://")
        assert s["documents"]