import json
from datetime import date
from pathlib import Path

SCHEMES_PATH = Path(__file__).parent.parent / "data" / "schemes.json"


def load_schemes() -> list[dict]:
    with open(SCHEMES_PATH, encoding="utf-8") as f:
        return json.load(f)


def age_from_birth_year(birth_year: int, today: date | None = None) -> int:
    # Only the birth year is stored, so this can be off by one.
    today = today or date.today()
    return today.year - birth_year


def check_eligibility(birth_year: int, tags: set[str] | None = None,
                      today: date | None = None) -> list[dict]:
    """Match one person against every scheme.

    tags: facts we know are true, e.g. {"bpl"} or {"income_tax_payer"}.
    status is one of: may_be_eligible, check_needed, not_eligible.
    """
    tags = tags or set()
    age = age_from_birth_year(birth_year, today)
    results = []

    for s in load_schemes():
        rules = s.get("rules", {})
        reasons, confirm = [], []
        status = "may_be_eligible"

        min_age, max_age = rules.get("min_age"), rules.get("max_age")
        if min_age is not None and age < min_age:
            status = "not_eligible"
            reasons.append(f"age {age} is below the minimum of {min_age}")
        elif max_age is not None and age > max_age:
            status = "not_eligible"
            reasons.append(f"age {age} is above the maximum of {max_age}")
        else:
            reasons.append(f"age {age} fits the age rule")

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


        if status == "not_eligible":
            confirm = []

        results.append({
            "scheme_id": s["id"],
            "name": s["name"],
            "status": status,
            "reasons": reasons,
            "confirm": confirm,
            "source_url": s["source_url"],
        })
       
    return results