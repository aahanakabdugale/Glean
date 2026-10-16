# Schemes Reference & Eligibility Engine

Glean checks family members against government welfare and savings schemes using a deterministic rules engine. All scheme definitions are loaded from [`data/schemes.json`](../data/schemes.json).

---

## 1. Scheme Schema (`data/schemes.json`)

Each entry in `data/schemes.json` is a JSON object with the following fields:

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Short unique slug used in tools and database records (e.g. `"scss"`, `"pm_kisan"`). |
| `name` | `str` | Full official display title. |
| `state` | `str` | Applicable state jurisdiction or `"All India"`. |
| `summary` | `str` | One-sentence summary of the scheme's benefit. |
| `rules` | `dict` | Eligibility criteria evaluated by the engine (see Rule Keys below). |
| `documents` | `list[str]` | Documents typically required to apply. |
| `notes` | `str` | Policy nuances, exceptions, and administrative notes. |
| `source_url` | `str` | Authoritative official government portal link. |
| `apply_url` | `str` | Online application or registration link. |

---

## 2. Rule Keys (Inside `"rules"`)

The engine evaluates rules using integer age calculations based on birth year (`age = today.year - birth_year`):

- **`min_age`** (`int`, optional): Person must be at least this age. If the person is under this age by $\le 3$ years and meets all non-age rules, they qualify for **Temporal Eligibility** (`almost_eligible`).
- **`max_age`** (`int`, optional): Person must be no older than this age. Exceeding `max_age` produces `not_eligible` (maximum age never qualifies for temporal eligibility).
- **`requires`** (`list[str]`, optional): Attribute tags that must be confirmed (e.g. `["bpl"]`, `["bank_account"]`, `["farmer"]`, `["girl_child"]`). If unconfirmed in the query, the status becomes `check_needed`.
- **`excludes`** (`list[str]`, optional): Disqualifying tags (e.g. `["income_tax_payer"]`). If any excluded tag is present, the status immediately becomes `not_eligible`.

Any rule key can be omitted when not applicable.

---

## 3. The Four Eligibility Statuses

| Status | Code Key | Meaning | Extra Fields Generated |
|---|---|---|---|
| **May Be Eligible** | `may_be_eligible` | Age meets criteria, required tags confirmed, no disqualifying tags present. | None |
| **Almost Eligible** | `almost_eligible` | Fails *only* the `min_age` requirement today, but will qualify within `ALMOST_ELIGIBLE_WINDOW_YEARS` (1 to 3 years), and non-age conditions are satisfied. | `years_until_eligible`<br>`eligible_from_year`<br>`spoken_hint`<br>`suggested_task` |
| **Check Needed** | `check_needed` | Age is eligible or almost eligible, but one or more required tags (`requires`) remain unconfirmed. | `confirm` (list of missing tags) |
| **Not Eligible** | `not_eligible` | Age is beyond `max_age`, age gap exceeds 3 years, or a disqualifying tag (`excludes`) is present. | `reasons` ("Why Not" explanations) |

---

## 4. Live Scheme Catalog (8 Schemes)

Glean tracks 8 central and state welfare initiatives covering senior citizens, children, working adults, and farmers:

### 1. Senior Citizens Savings Scheme (`scss`)
- **Category:** Senior Citizens / Savings
- **Jurisdiction:** All India
- **Rules:** `min_age: 60`
- **Key Documents:** Age proof, Identity/Address proof (PAN, Passport, Voter ID), Passport photos
- **Official Source:** [SBI Senior Citizens Savings Scheme](https://sbi.bank.in/web/personal-banking/investments-deposits/govt-schemes/senior-citizens-savings-scheme)

### 2. Ayushman Vay Vandana Card (`ayushman_vay_vandana`)
- **Category:** Senior Healthcare Cover (AB PM-JAY)
- **Jurisdiction:** All India
- **Rules:** `min_age: 70`
- **Key Documents:** Aadhaar card (age verified via Aadhaar e-KYC), Mobile number
- **Official Source:** [Rajya Sabha Parliamentary Record / NHA](https://rsdebate.nic.in/bitstream/123456789/758871/1/PQ_267_11022025_U903_p367_p370.pdf)

### 3. Indira Gandhi National Old Age Pension Scheme (`ignoaps_mh`)
- **Category:** Social Welfare Pension
- **Jurisdiction:** Maharashtra
- **Rules:** `min_age: 65`, `requires: ["bpl"]`
- **Key Documents:** Age proof, BPL certificate, Bank account details
- **Official Source:** [Nashik District Collectorate / SJSA](https://nashik.gov.in/en/scheme/indira-gandhi-national-old-age-pension-scheme/)

### 4. Atal Pension Yojana (`apy`)
- **Category:** Guaranteed Monthly Pension (Unorganized Sector)
- **Jurisdiction:** All India
- **Rules:** `min_age: 18`, `max_age: 40`, `excludes: ["income_tax_payer"]`
- **Key Documents:** Savings bank account, Mobile number, Aadhaar, Nominee details
- **Official Source:** [PFRDA APY Guidelines](https://pfrda.org.in/web/pfrda/w/faqs/atal-pension-yojana)

### 5. Pradhan Mantri Jeevan Jyoti Bima Yojana (`pmjjby`)
- **Category:** Term Life Insurance (Rs 2 Lakh cover)
- **Jurisdiction:** All India
- **Rules:** `min_age: 18`, `max_age: 50`, `requires: ["bank_account"]`
- **Key Documents:** Aadhaar card, Savings bank account, Auto-debit consent form
- **Official Source:** [Department of Financial Services](https://financialservices.gov.in/beta/en/insurance-divisions)

### 6. Pradhan Mantri Suraksha Bima Yojana (`pmsby`)
- **Category:** Accidental Death & Disability Insurance (Rs 2 Lakh cover)
- **Jurisdiction:** All India
- **Rules:** `min_age: 18`, `max_age: 70`, `requires: ["bank_account"]`
- **Key Documents:** Aadhaar card, Bank/Post office passbook, Nominee details
- **Official Source:** [Department of Financial Services](https://financialservices.gov.in/beta/en/insurance-divisions)

### 7. Sukanya Samriddhi Yojana (`ssy`)
- **Category:** Girl Child Small Savings & Higher Education Fund
- **Jurisdiction:** All India
- **Rules:** `max_age: 10`, `requires: ["girl_child"]`
- **Key Documents:** Birth certificate of girl child, Parent/guardian ID & address proof, Photos
- **Official Source:** [India Post SSY Guidelines](https://www.indiapost.gov.in/Financial/Pages/Content/SSY.aspx)

### 8. PM Kisan Samman Nidhi (`pm_kisan`)
- **Category:** Direct Income Support for Farmers (Rs 6,000/yr)
- **Jurisdiction:** All India
- **Rules:** `min_age: 18`, `requires: ["farmer"]`, `excludes: ["income_tax_payer"]`
- **Key Documents:** Aadhaar card, Land record / Record of Rights (Khasra/Khatauni), Aadhaar-linked bank passbook
- **Official Source:** [PM-KISAN National Portal](https://pmkisan.gov.in/)

---

## 5. Python API Usage

```python
import datetime
from glean.schemes import check_eligibility

# Example 1: Justin (born 1968, age 58 in 2026) -> Within 3 yrs of SCSS (min_age 60)
results = check_eligibility(
    birth_year=1968,
    tags={"bank_account"},
    today=datetime.date(2026, 10, 15),
    member_name="Justin",
)

for r in results:
    print(f"[{r['status'].upper()}] {r['name']}")
    if r["status"] == "almost_eligible":
        print(f"  -> Spoken Hint: {r['spoken_hint']}")
        print(f"  -> Suggested Task: {r['suggested_task']['title']} ({r['suggested_task']['due_year']})")
    elif r["status"] == "not_eligible":
        print(f"  -> Why Not: {', '.join(r['reasons'])}")
```

### Result Dictionary Structure

```json
{
  "scheme_id": "scss",
  "name": "Senior Citizens Savings Scheme",
  "status": "almost_eligible",
  "reasons": ["age 58 is below the minimum of 60"],
  "confirm": [],
  "source_url": "https://sbi.bank.in/...",
  "years_until_eligible": 2,
  "eligible_from_year": 2028,
  "spoken_hint": "Justin is not eligible for Senior Citizens Savings Scheme today, but may qualify around 2028.",
  "suggested_task": {
    "title": "Check eligibility for Senior Citizens Savings Scheme",
    "due_year": 2028
  }
}
```

---

## 6. Adding a New Scheme

1. Open [`data/schemes.json`](../data/schemes.json) and add a new object to the array.
2. Fill every field; copy an existing entry as a template.
3. Every scheme **must** have a valid, working `.gov.in` or official institution `source_url`.
4. Run the test suite:
   ```powershell
   .\.venv\Scripts\pytest
   ```
5. Run the scenario benchmark:
   ```powershell
   .\.venv\Scripts\python eval_scenarios.py
   ```

---

> **Disclaimer:** Glean provides assistive guidance only. Eligibility rules, income caps, and documentation criteria may change over time. Users must always verify official criteria on the government portal linked in `source_url` before submitting formal applications.
