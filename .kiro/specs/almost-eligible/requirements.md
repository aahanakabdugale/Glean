# Requirements — Almost Eligible (Temporal Eligibility)

## Overview

`check_scheme_eligibility` currently returns one of three statuses:
`may_be_eligible`, `check_needed`, or `not_eligible`.  This spec adds a fourth
outcome — `almost_eligible` — for a person who fails only a scheme's minimum-age
rule today but will reach that age within a configurable window (default 3 years).

Responses must remain short, plain, and readable aloud.

---

## Glossary

| Term | Meaning |
|---|---|
| `almost_eligible` | Person fails only the minimum-age criterion; every other criterion passes; and the gap is within `ALMOST_ELIGIBLE_WINDOW_YEARS`. |
| `ALMOST_ELIGIBLE_WINDOW_YEARS` | Named constant (value: `3`). Never a magic number. |
| `eligible_from_year` | `birth_year + min_age` — the calendar year in which the person will reach the minimum age. |
| `years_until_eligible` | `min_age − current_age` (always 1–3 for `almost_eligible`). |

---

## Functional Requirements

### FR-AE-1 · Almost-eligible rule

WHEN a scheme has a `min_age` rule AND the person's current age is less than
`min_age` AND `(min_age − current_age)` is between 1 and
`ALMOST_ELIGIBLE_WINDOW_YEARS` (inclusive) AND every non-age criterion
(requires, excludes) already passes or is unknown in the permissive direction,
THE SYSTEM SHALL set the scheme's status to `"almost_eligible"`.

### FR-AE-2 · Boundary: window edge cases

WHEN `(min_age − current_age)` equals exactly `ALMOST_ELIGIBLE_WINDOW_YEARS`
(i.e. 3), THE SYSTEM SHALL return `almost_eligible`.

WHEN `(min_age − current_age)` equals `ALMOST_ELIGIBLE_WINDOW_YEARS + 1` or
more (i.e. 4+), THE SYSTEM SHALL return `not_eligible` (unchanged behaviour).

WHEN the person's age equals `min_age`, THE SYSTEM SHALL return `may_be_eligible`
(or `check_needed`), never `almost_eligible`.

WHEN the person's age exceeds `min_age`, THE SYSTEM SHALL return `may_be_eligible`
(or `check_needed`), never `almost_eligible`.

### FR-AE-3 · Maximum-age rules never produce almost_eligible

WHEN a scheme has a `max_age` rule AND the person's age exceeds `max_age`, THE
SYSTEM SHALL return `not_eligible`.  The `almost_eligible` status MUST NOT be
applied to maximum-age failures under any circumstances.

### FR-AE-4 · Non-age criteria gate almost_eligible

WHEN any non-age criterion fails — for example the person has a tag listed in
`excludes`, THE SYSTEM SHALL set the status to `not_eligible`, not
`almost_eligible`.

WHEN a required tag (from `requires`) is absent from the provided tags, THE
SYSTEM SHALL set the status to `check_needed` even if the age gap would otherwise
qualify for `almost_eligible`.  The caller did not confirm that criterion, so
almost-eligible cannot be guaranteed.

**Unknown data handling:** tags not present in the call are treated as unknown,
not as false.  An unknown `requires` tag moves the result to `check_needed`; it
does not block `almost_eligible` in the same way a failed `excludes` tag does.
Specifically: if the only failure is minimum age AND all `requires` tags are
either confirmed present (in the passed tags set) OR absent from both the tags
set and the scheme's `requires` list (i.e. there are no unconfirmed `requires`
tags for schemes that have a `requires` rule), the result is `almost_eligible`.
If there are unconfirmed `requires` tags, the result is `check_needed`.

### FR-AE-5 · Output shape — new fields for almost_eligible

WHEN the status is `almost_eligible`, THE SYSTEM SHALL include these additional
fields alongside the existing fields:

| Field | Type | Description |
|---|---|---|
| `years_until_eligible` | int | `min_age − current_age` (1–3) |
| `eligible_from_year` | int | `birth_year + min_age` |
| `source_url` | str | Official URL from the scheme record |
| `suggested_task` | dict | `{"title": str, "due_year": int}` — a task the AI may offer to the user |
| `spoken_hint` | str | A short, voice-friendly sentence (see FR-AE-7) |

WHEN the status is anything other than `almost_eligible`, THE SYSTEM SHALL NOT
add these extra fields (existing callers must not break).

### FR-AE-6 · Existing output fields preserved

WHEN `check_scheme_eligibility` is called, THE SYSTEM SHALL return all fields
currently present in each result dict: `scheme_id`, `name`, `status`, `reasons`,
`confirm`, `source_url`.  These fields MUST NOT be renamed or removed.

### FR-AE-7 · Spoken hint

WHEN the status is `almost_eligible`, THE SYSTEM SHALL include a `spoken_hint`
field containing a short sentence in the form:

> "<Person name> is not eligible for <Scheme name> today, but may qualify around
> <eligible_from_year>."

The person's name is not available inside `schemes.py`; THE SYSTEM SHALL accept
an optional `member_name: str = ""` parameter in `check_eligibility()` and use it
to populate the spoken hint.  When `member_name` is empty, the hint MUST use a
generic form: "Not eligible today, but may qualify around <eligible_from_year>."

### FR-AE-8 · Eligibility language — no guarantees

WHEN returning any result, THE SYSTEM SHALL use "may be eligible" / "may qualify"
language.  THE SYSTEM SHALL NOT use language that guarantees eligibility.

THE SYSTEM SHALL append "Guidance only, verify on the official site." to the final
formatted output in `check_scheme_eligibility` (this is already present; it must
not be removed).

### FR-AE-9 · Suggested task — suggestion only

WHEN the status is `almost_eligible`, THE SYSTEM SHALL include a `suggested_task`
dict in the result.  This is a recommendation only.  THE SYSTEM SHALL NOT create
a task record automatically.  A task is created only if the user explicitly
requests it, at which point the caller passes the suggestion to the existing
`add_task` tool.

The `suggested_task` dict format:
```json
{
  "title": "Check eligibility for Senior Citizens Savings Scheme",
  "due_year": 2028
}
```

### FR-AE-10 · Injectable current year

WHEN `check_eligibility()` is called, THE SYSTEM SHALL accept an optional
`today: date | None = None` parameter (already present) and use it as the
reference date for all age calculations.  Tests MUST pass an explicit `today`
value and MUST NOT depend on the real system clock.

### FR-AE-11 · No new scheme rules

THE SYSTEM SHALL NOT add new entries or new rule fields to `data/schemes.json`
as part of this feature.  `almost_eligible` is computed only from rules already
present.  If a new scheme rule is needed in the future (for example "enhanced
pension at age 75"), it MUST have a real `source_url` before being added.

### FR-AE-12 · Result ordering

WHEN `check_scheme_eligibility` formats its output, THE SYSTEM SHALL group
results in this order:

1. `may_be_eligible` (fully eligible)
2. `check_needed`
3. `almost_eligible` — soonest `eligible_from_year` first within this group
4. `not_eligible`

---

## Acceptance Criteria

### AC-AE-1 · Core almost_eligible trigger

WHEN `check_eligibility` is called with `birth_year=1966` (age 60 under TODAY =
2026-10-06) for SCSS (min_age 60), THE SYSTEM SHALL return `may_be_eligible`
(age exactly 60 → eligible, not almost).

WHEN called with `birth_year=1967` (age 59), THE SYSTEM SHALL return
`almost_eligible` for SCSS (1 year away, within window).

WHEN called with `birth_year=1969` (age 57), THE SYSTEM SHALL return
`almost_eligible` for SCSS (3 years away, at window boundary).

WHEN called with `birth_year=1970` (age 56), THE SYSTEM SHALL return
`not_eligible` for SCSS (4 years away, outside window).

### AC-AE-2 · years_until_eligible and eligible_from_year

WHEN `birth_year=1969` and SCSS `min_age=60`, THE SYSTEM SHALL return
`years_until_eligible=3` and `eligible_from_year=2029`.

### AC-AE-3 · Max-age schemes never produce almost_eligible

WHEN APY (`max_age=40`) and `birth_year=1985` (age 41), THE SYSTEM SHALL return
`not_eligible`, not `almost_eligible`.

### AC-AE-4 · Non-age failure blocks almost_eligible

WHEN IGNOAPS_MH (`min_age=65`, `requires=["bpl"]`) and `birth_year=1963` (age 63,
2 years away) and `tags={"income_tax_payer"}` (no bpl), THE SYSTEM SHALL return
`check_needed` (bpl unconfirmed), not `almost_eligible`.

### AC-AE-5 · Excludes tag blocks almost_eligible

WHEN APY (`excludes=["income_tax_payer"]`, `min_age=18`) and `birth_year=2010`
(age 16, 2 years away) and `tags={"income_tax_payer"}`, THE SYSTEM SHALL return
`not_eligible`, not `almost_eligible`.

### AC-AE-6 · Missing birth_year / future birth_year

WHEN `birth_year` is in the future (e.g. `birth_year=2030`, today 2026), the
computed age is negative; THE SYSTEM SHALL return `not_eligible` for all
min-age schemes and MUST NOT raise an exception.

### AC-AE-7 · Mixed results for one person

WHEN a person is `may_be_eligible` for Ayushman Vay Vandana and `almost_eligible`
for SCSS, both results MUST appear in the output and MUST be formatted in the
correct group order (eligible first, then almost_eligible).

### AC-AE-8 · Backward compatibility

WHEN the 73 existing tests are run unchanged after the feature is implemented,
THE SYSTEM SHALL pass all 73 without modification.

---

## Edge Cases

| Edge Case | Expected Behaviour |
|---|---|
| Age gap exactly 3 (window boundary) | `almost_eligible` |
| Age gap exactly 4 | `not_eligible` |
| Age exactly equal to `min_age` | `may_be_eligible` (not almost) |
| Age already above `min_age` | `may_be_eligible` or `check_needed` |
| `birth_year` missing or `None` | Caller must validate; `check_eligibility` expects an int; callers that might pass `None` must guard against it |
| `birth_year` in the future | Age is negative → `not_eligible` for all min-age schemes |
| Person fails `excludes` while age is close | `not_eligible` |
| Person has unconfirmed `requires` while age is close | `check_needed` |
| Mixed statuses for one person | All four statuses may coexist; ordering rule applies |
| Max-age failure | `not_eligible` only; never `almost_eligible` |
| `member_name` empty | Spoken hint uses generic phrasing |

---

## Out of Scope (this iteration)

- Adding new scheme data or new scheme rule fields.
- Storing "almost eligible" state in the database.
- Proactive notifications when a person becomes eligible.
- Age ranges that involve full birth dates (we only have `birth_year`).
- UI changes.
