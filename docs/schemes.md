# Schemes reference

## Fields in each scheme (data/schemes.json)

| Field        | What it means                                           |
|--------------|---------------------------------------------------------|
| `id`         | Short unique key used in code, e.g. `"apy"`            |
| `name`       | Full display name                                       |
| `state`      | State it applies to, or `"All India"`                   |
| `summary`    | One-sentence description                                |
| `rules`      | Age limits and tag conditions (see below)               |
| `documents`  | Documents typically needed to apply                     |
| `notes`      | Extra details not captured by the rules                 |
| `source_url` | Official government page                                |
| `apply_url`  | Where to start the application                          |

## Rule keys (inside `"rules"`)

- **`min_age`** — person must be at least this age.
- **`max_age`** — person must be no older than this age.
- **`requires`** — tags that must be true, e.g. `["bpl"]`. Any missing
  tag changes the status to `check_needed`.
- **`excludes`** — tags that disqualify the person, e.g.
  `["income_tax_payer"]`. Any present tag changes the status to
  `not_eligible`.

Any rule key can be omitted when it does not apply.

## The three statuses

| Status            | Meaning                                                    |
|-------------------|------------------------------------------------------------|
| `may_be_eligible` | Age fits and no disqualifying tags — worth applying        |
| `check_needed`    | Age fits but a required tag has not been confirmed yet     |
| `not_eligible`    | Age is out of range, or a disqualifying tag is present     |

When the status is `not_eligible`, the `confirm` list is always empty.

## Calling check_eligibility

```python
from glean.schemes import check_eligibility

results = check_eligibility(birth_year=1958, tags={"bpl"})
for r in results:
    print(r["name"], "→", r["status"])
    if r["confirm"]:
        print("  Still need:", r["confirm"])
```

Pass `tags` as a set of known facts. Omit it (or pass `set()`) if
nothing is known yet. Each result has: `scheme_id`, `name`, `status`,
`reasons`, `confirm`, `source_url`.

## Adding a new scheme

1. Open `data/schemes.json` and add a new object to the array.
2. Fill every field; copy an existing entry as a template.
3. Set `"rules"` to `{}` if there are no age or tag conditions.
4. Run `pytest` to confirm nothing is broken.

Minimal example:
```json
{
  "id": "my_scheme", "name": "My Scheme", "state": "All India",
  "summary": "Short description.", "rules": { "min_age": 60 },
  "documents": ["Age proof"], "notes": "",
  "source_url": "https://example.gov.in/scheme",
  "apply_url": "https://example.gov.in/apply"
}
```

---

> **Disclaimer:** This tool gives guidance only. Rules can change and
> edge cases may not be captured. Always verify on the official site
> linked in `source_url` before applying.
