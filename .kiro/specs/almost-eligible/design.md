# Design — Almost Eligible (Temporal Eligibility)

## Summary

This feature adds a fourth eligibility status, `almost_eligible`, to the
existing `check_eligibility()` function in `glean/schemes.py`.  No new tables,
no new tools, and no new schemes data are required.

---

## Change Points

### `glean/schemes.py` — `check_eligibility()`

This is the only function that changes in the core logic layer.

**Signature change (additive, backward-compatible):**
```python
def check_eligibility(
    birth_year: int,
    tags: set[str] | None = None,
    today: date | None = None,
    member_name: str = "",          # NEW — used only for spoken_hint
) -> list[dict]:
```

**New constant (module level):**
```python
ALMOST_ELIGIBLE_WINDOW_YEARS = 3   # schemes within this many years are "almost eligible"
```

**Logic change inside the per-scheme loop:**

After computing `age` and before appending to `results`, insert the
almost-eligible branch between the existing `not_eligible` path and the final
append:

```
current logic (simplified):
  if age < min_age → not_eligible
  elif age > max_age → not_eligible
  else → age fits; check requires/excludes

new logic:
  if age < min_age:
      gap = min_age - age
      if 1 <= gap <= ALMOST_ELIGIBLE_WINDOW_YEARS:
          # Tentatively almost_eligible — check non-age criteria next
          tentative = "almost_eligible"
      else:
          status = "not_eligible"
  elif max_age is not None and age > max_age:
      status = "not_eligible"          # max-age failure → never almost_eligible
  else:
      tentative = "may_be_eligible"    # age fits

  # Only enter non-age checks if not already not_eligible
  if status != "not_eligible":
      for tag in excludes:
          if tag in tags:
              status = "not_eligible"  # hard block — clears tentative
      if status != "not_eligible":
          for tag in requires:
              if tag not in tags:
                  status = "check_needed"   # unconfirmed required tag
      if status not in ("not_eligible", "check_needed"):
          status = tentative   # either may_be_eligible or almost_eligible
```

**Extra fields appended only for `almost_eligible`:**
```python
if status == "almost_eligible":
    eligible_from_year = birth_year + min_age
    years_until = min_age - age
    hint = (
        f"{member_name} is not eligible for {s['name']} today, "
        f"but may qualify around {eligible_from_year}."
        if member_name
        else f"Not eligible today, but may qualify around {eligible_from_year}."
    )
    result.update({
        "years_until_eligible": years_until,
        "eligible_from_year":   eligible_from_year,
        "spoken_hint":          hint,
        "suggested_task": {
            "title":    f"Check eligibility for {s['name']}",
            "due_year": eligible_from_year,
        },
    })
```

### `glean/tools.py` — `check_scheme_eligibility()`

Two small changes:

1. Pass `member_name=member["name"]` through to `schemes.check_eligibility()`.
2. Add a new formatting block between `check_needed` and `not_eligible` for
   `almost_eligible` results, ordered by `eligible_from_year` ascending.

No change to the tool's signature or its validation logic.

---

## New Output Shape

### Per-scheme result dict (existing fields unchanged)

```json
{
  "scheme_id":   "scss",
  "name":        "Senior Citizens Savings Scheme",
  "status":      "almost_eligible",
  "reasons":     ["age 57 is below the minimum of 60"],
  "confirm":     [],
  "source_url":  "https://sbi.bank.in/...",

  "years_until_eligible": 3,
  "eligible_from_year":   2029,
  "spoken_hint":          "Justin is not eligible for Senior Citizens Savings Scheme today, but may qualify around 2029.",
  "suggested_task": {
    "title":    "Check eligibility for Senior Citizens Savings Scheme",
    "due_year": 2029
  }
}
```

The four new keys (`years_until_eligible`, `eligible_from_year`, `spoken_hint`,
`suggested_task`) are present **only** when `status == "almost_eligible"`.
All other status values return the existing six keys only.

---

## Decision Table — Age vs Status

The table uses SCSS as the example (min_age = 60, no max_age).

| current_age | gap | `requires` met? | `excludes` absent? | status |
|---|---|---|---|---|
| 61 | — | yes | yes | `may_be_eligible` |
| 60 | 0 | yes | yes | `may_be_eligible` |
| 59 | 1 | yes | yes | `almost_eligible` |
| 58 | 2 | yes | yes | `almost_eligible` |
| 57 | 3 | yes | yes | `almost_eligible` |
| 56 | 4 | — | — | `not_eligible` |
| 59 | 1 | no (unconfirmed) | yes | `check_needed` |
| 59 | 1 | yes | no (excluded) | `not_eligible` |

For APY (min_age = 18, **max_age = 40**, excludes income_tax_payer):

| current_age | gap | note | status |
|---|---|---|---|
| 41 | — | over max_age | `not_eligible` |
| 40 | — | within range | `may_be_eligible` |
| 17 | 1 | age below min | `almost_eligible` |
| 16 | 2 | age below min | `almost_eligible` |
| 15 | 3 | age below min | `almost_eligible` |
| 14 | 4 | too far | `not_eligible` |
| 17 | 1 | excluded by tag | `not_eligible` |

---

## Result Ordering in `check_scheme_eligibility`

The tool already separates results into `eligible`, `check_needed`, and
`not_eligible` buckets.  Add `almost_eligible` between `check_needed` and
`not_eligible`:

```
1. may_be_eligible   — formatted as "May be eligible:"
2. check_needed      — formatted as "Requires verification:"
3. almost_eligible   — formatted as "Coming up soon:", sorted by eligible_from_year asc
4. not_eligible      — formatted as "Not eligible:"
```

---

## Connection to `family_brief`

`family_brief` calls `schemes.check_eligibility(m_birth)` and already groups by
`may_be_eligible` and `check_needed`.  After this feature ships, it should also
handle `almost_eligible`:

- In the personalised path, surface `almost_eligible` results under a "Coming up
  soon" heading alongside the spoken hint.
- Pass `member_name=m_name` to `check_eligibility()` so hints are personalised.

This is **out of scope for this spec** but the `family_brief` change is a
one-liner once `check_eligibility` is updated; note it here so the implementer
does not forget.

---

## Connection to `plan_scheme_application`

`plan_scheme_application` currently requires the person to be `may_be_eligible`.
After this feature ships, the tool should accept `almost_eligible` schemes too,
scheduling tasks for the `eligible_from_year` rather than an immediate deadline.

This is **out of scope for this spec** but worth noting for future iteration.

---

## What Is Not Changing

| Item | Why unchanged |
|---|---|
| `data/schemes.json` | No new rules; `almost_eligible` is derived from existing `min_age` fields |
| `glean/db.py` | No new tables or columns |
| `glean/app.py` | No changes to the FastMCP instance |
| `server.py` | No startup changes |
| Tool signature of `check_scheme_eligibility` | Additive only — same parameters, same return type (str) |
| All 73 existing tests | No modifications; all must continue to pass |

---

## Testing Approach

- `tests/test_schemes.py` and `tests/test_schemes_extra.py` are not modified.
- New tests go in `tests/test_almost_eligible.py`.
- All tests use a fixed `TODAY = date(2026, 10, 6)` (same convention as existing
  tests) and pass it explicitly so the suite is deterministic.
- Tests call `check_eligibility()` directly, not via the MCP layer.
- Edge-case tests follow the boundary table in requirements.md.

---

## Risks and Notes

| Risk | Mitigation |
|---|---|
| Age arithmetic off-by-one (birth_year only, no full DOB) | The `age_from_birth_year` helper already documents this; results say "in about N years", never an exact date |
| Future change to `schemes.json` silently creates new `almost_eligible` results | Acceptable — the rule is general by design |
| Adding a new scheme with `requires` where the tag is unknown for most users | Result would be `check_needed`, not `almost_eligible`; correct and safe |
