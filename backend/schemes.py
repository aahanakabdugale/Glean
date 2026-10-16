import json
from datetime import date
from pathlib import Path

SCHEMES_PATH = Path(__file__).parent.parent / "data" / "schemes.json"
ALMOST_ELIGIBLE_WINDOW_YEARS = 3


def load_schemes() -> list[dict]:
    with open(SCHEMES_PATH, encoding="utf-8") as f:
        return json.load(f)


def age_from_birth_year(birth_year: int, today: date | None = None) -> int:
    # Only the birth year is stored, so this can be off by one.
    today = today or date.today()
    return today.year - birth_year


def check_eligibility(
    birth_year: int,
    tags: set[str] | None = None,
    today: date | None = None,
    member_name: str = "",
) -> list[dict]:
    """Match one person against every scheme.

    tags: facts we know are true, e.g. {"bpl"} or {"income_tax_payer"}.
    status is one of: may_be_eligible, check_needed, almost_eligible, not_eligible.
    """
    tags = tags or set()
    age = age_from_birth_year(birth_year, today)
    results = []

    for s in load_schemes():
        rules = s.get("rules", {})
        reasons, confirm = [], []
        status = None
        tentative = "may_be_eligible"

        min_age, max_age = rules.get("min_age"), rules.get("max_age")
        if min_age is not None and age < min_age:
            gap = min_age - age
            if 1 <= gap <= ALMOST_ELIGIBLE_WINDOW_YEARS:
                tentative = "almost_eligible"
                reasons.append(f"age {age} is below the minimum of {min_age}")
            else:
                status = "not_eligible"
                reasons.append(f"age {age} is below the minimum of {min_age}")
        elif max_age is not None and age > max_age:
            status = "not_eligible"
            reasons.append(f"age {age} is above the maximum of {max_age}")
        else:
            reasons.append(f"age {age} fits the age rule")

        if status != "not_eligible":
            for tag in rules.get("excludes", []):
                if tag in tags:
                    status = "not_eligible"
                    reasons.append(f"not allowed if: {tag}")
                else:
                    confirm.append(f"confirm this is NOT true: {tag}")

            if status != "not_eligible":
                for tag in rules.get("requires", []):
                    if tag not in tags:
                        status = "check_needed"
                        confirm.append(f"needs: {tag}")

            if status not in ("not_eligible", "check_needed"):
                status = tentative

        if status == "not_eligible":
            confirm = []

        res_dict = {
            "scheme_id": s["id"],
            "name": s["name"],
            "status": status,
            "reasons": reasons,
            "confirm": confirm,
            "source_url": s["source_url"],
        }

        if status == "almost_eligible":
            eligible_from_year = birth_year + min_age
            years_until = min_age - age
            hint = (
                f"{member_name} is not eligible for {s['name']} today, but may qualify around {eligible_from_year}."
                if member_name
                else f"Not eligible today, but may qualify around {eligible_from_year}."
            )
            res_dict.update({
                "years_until_eligible": years_until,
                "eligible_from_year": eligible_from_year,
                "spoken_hint": hint,
                "suggested_task": {
                    "title": f"Check eligibility for {s['name']}",
                    "due_year": eligible_from_year,
                },
            })

        results.append(res_dict)

    return results