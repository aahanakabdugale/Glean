# Tasks — Almost Eligible (Temporal Eligibility)

Tasks are ordered so tests are written before or alongside the code they cover.
Each task is small and self-contained.  Work top-to-bottom; later tasks depend on
earlier ones passing.

---

## T-AE-01 · Add ALMOST_ELIGIBLE_WINDOW_YEARS constant

**File:** `glean/schemes.py`

- Add `ALMOST_ELIGIBLE_WINDOW_YEARS = 3` at module level, immediately after the
  imports.
- Do not change any other code in this task.

**Done when:**
```
python -c "from glean.schemes import ALMOST_ELIGIBLE_WINDOW_YEARS; assert ALMOST_ELIGIBLE_WINDOW_YEARS == 3"
```
exits with no error.

---

## T-AE-02 · Write skeleton tests (red) for almost_eligible

**File:** `tests/test_almost_eligible.py` (new file)

Create the file with:
- Module-level `TODAY = date(2026, 10, 6)` and a `by_id` helper (same pattern as
  `test_schemes.py`).
- One test class `TestAlmostEligibleCore` with the following test stubs — each
  must fail (`assert False, "not implemented"`) so the red state is visible:
  - `test_exactly_1_year_away_is_almost` — birth_year=1965, SCSS
  - `test_exactly_3_years_away_is_almost` — birth_year=1969 (age 57), SCSS
  - `test_exactly_4_years_away_is_not_eligible` — birth_year=1970 (age 56), SCSS
  - `test_at_min_age_is_eligible_not_almost` — birth_year=1966 (age 60), SCSS
  - `test_above_min_age_is_eligible_not_almost` — birth_year=1960 (age 66), SCSS
  - `test_almost_eligible_fields_present` — verify `years_until_eligible`,
    `eligible_from_year`, `spoken_hint`, `suggested_task` in result
  - `test_years_until_and_from_year_values` — birth_year=1969, SCSS:
    `years_until_eligible==3`, `eligible_from_year==2029`
  - `test_max_age_failure_never_almost` — birth_year=1985 (age 41), APY
  - `test_excludes_tag_blocks_almost` — APY, birth_year=2010 (age 16), tags={"income_tax_payer"}
  - `test_unconfirmed_requires_gives_check_needed_not_almost` — IGNOAPS_MH,
    birth_year=1963 (age 63), tags={} (bpl unknown)
  - `test_future_birth_year_not_eligible` — birth_year=2030, SCSS
  - `test_non_almost_result_has_no_extra_fields` — existing may_be_eligible result
    must not have `years_until_eligible` key
  - `test_ordering_eligible_before_almost` — person with mixed statuses:
    almost_eligible for SCSS, may_be_eligible for Ayushman — eligible appears first

- One test class `TestSpokenHint`:
  - `test_spoken_hint_with_name` — member_name="Justin"; hint contains "Justin" and "2029"
  - `test_spoken_hint_without_name` — member_name=""; hint contains "may qualify around"
    and does not start with "Justin" or another name

- One test class `TestSuggestedTask`:
  - `test_suggested_task_shape` — verify keys `title` (str) and `due_year` (int)
  - `test_suggested_task_due_year_matches_eligible_from_year`

- One test class `TestBackwardCompat`:
  - `test_existing_result_keys_unchanged` — run `check_eligibility(1970, set(), TODAY)`
    and assert every result contains the original six keys
  - `test_original_statuses_still_valid` — assert no result has status
    `almost_eligible` for a birth_year where none was expected (birth_year=1950,
    tags={"bpl"} — all four schemes should be their original statuses)

**Done when:** `pytest tests/test_almost_eligible.py` runs and **fails** (red —
stubs not yet implemented).

---

## T-AE-03 · Implement almost_eligible in check_eligibility()

**File:** `glean/schemes.py`

- Update the `check_eligibility()` function signature to add
  `member_name: str = ""` (keep all existing parameters and defaults unchanged).
- Inside the per-scheme loop, replace the `if age < min_age → not_eligible` block
  with the full logic described in `design.md` under "Logic change inside the
  per-scheme loop".
- Append the four extra fields (`years_until_eligible`, `eligible_from_year`,
  `spoken_hint`, `suggested_task`) to the result dict **only** when
  `status == "almost_eligible"`.
- Do NOT modify the return structure for any other status.

**Done when:**
```
pytest tests/test_almost_eligible.py tests/test_schemes.py tests/test_schemes_extra.py
```
passes with no failures.

---

## T-AE-04 · Update check_scheme_eligibility() tool to pass member_name

**File:** `glean/tools.py`

- In `check_scheme_eligibility`, pass `member_name=member["name"]` when calling
  `schemes.check_eligibility(...)`.
- Add a new formatting block between `check_needed` and `not_eligible` for the
  `almost_eligible` bucket:
  - Sort by `eligible_from_year` ascending before formatting.
  - Heading: `"\nComing up soon:"`
  - Each line: `"• {r['name']} — {r['spoken_hint']} Official link: {r['source_url']}"`
  - Offer the suggested task: append a line such as
    `"  → Suggested: {r['suggested_task']['title']} (around {r['suggested_task']['due_year']})"`

**Done when:** `pytest tests/test_almost_eligible.py` still passes (no regression
from the tool change) and a manual smoke call returns an `almost_eligible` section
in the output.

---

## T-AE-05 · Write tool-level tests for check_scheme_eligibility output

**File:** `tests/test_almost_eligible.py` — add a new test class
`TestCheckSchemeEligibilityTool` at the bottom

Reuse the existing `db_conn` fixture pattern from `tests/test_tools.py` (import
and monkeypatch `glean.db.get_connection`).

Tests to add:
- `test_tool_includes_almost_eligible_section` — add a member born 1969 (age 57),
  call `check_scheme_eligibility("Justin")`, assert output contains "Coming up soon"
  and "may qualify around 2029".
- `test_tool_ordering_eligible_before_almost` — add a member born 1956 (age 70,
  eligible for Ayushman and almost for SCSS at 57), assert "May be eligible"
  section appears before "Coming up soon" section.
- `test_tool_no_almost_section_when_not_applicable` — member born 1950 (age 76),
  assert output does NOT contain "Coming up soon".
- `test_tool_disclaimer_still_present` — assert "Guidance only" appears in every
  response.

**Done when:** `pytest tests/test_almost_eligible.py` passes all tests including
the new tool class.

---

## T-AE-06 · Verify no regression on the full test suite

**Files:** all tests

Run the complete pytest suite from the project root and record the counts:

```
pytest --tb=short -q
```

- Before this feature: 73 tests passing, 0 failing.
- After this feature: ≥ 73 existing tests still passing, plus the new tests
  passing.
- Record the before and after counts in `docs/friction-log.md` with the date
  and a note confirming no regressions.

**Done when:** `pytest` exits green with all tests passing and the count is
recorded in `docs/friction-log.md`.

---

## Checklist

- [ ] T-AE-01 · Constant added and importable
- [ ] T-AE-02 · Skeleton tests written and failing (red)
- [ ] T-AE-03 · `check_eligibility()` updated; all scheme tests green
- [ ] T-AE-04 · `check_scheme_eligibility` tool updated
- [ ] T-AE-05 · Tool-level tests written and passing
- [ ] T-AE-06 · Full suite green; before/after counts logged
