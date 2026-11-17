# Deterministic Eligibility Evaluation & Rule Engine Architecture

## 1. Architectural Philosophy: Determinism Over Generative Guessing
Statutory welfare eligibility under Indian administrative law requires exact, predictable, and explainable evaluation. The Scheme Navigator platform enforces strict separation between:
1. **Deterministic Rule Engine**: Encoded statutory criteria (age thresholds, income limits, domicile, caste categories, landholding sizes, municipal boundaries) are evaluated via a formal Abstract Syntax Tree (AST) parser in Python (`scheme_navigator.services.rule_engine`).
2. **Generative AI & LLMs**: AI models are restricted to assisting with document extraction, translation, and user-friendly explanation formatting. **Under no circumstances does an LLM decide, modify, or override a statutory eligibility predicate.**

---

## 2. Three-Valued Logic & Five Outcome Statuses
In real-world citizen guidance, incomplete information must never be treated as proof of ineligibility. The engine implements Kleene three-valued logic (`True`, `False`, `None`):

| Evaluation Status | Formal Semantics | Citizen Explanation |
|---|---|---|
| `ELIGIBLE` | All evaluated statutory conditions match `True`, and the scheme satisfies all fail-closed production eligibility gates. | **Eligible (पात्र)** — All mandatory requirements satisfied. Proceed to prepare application documents. |
| `PARTIAL` | Citizen meets the primary statutory requirements ($\ge 70\%$ pass ratio) but misses at most 2 secondary non-hard conditions. | **Exploratory Match (अंशतः जुळणारे)** — High likelihood of eligibility; secondary conditions pending verification. |
| `NEEDS_INFORMATION` | Profile is missing fields required to determine eligibility (`None`). Zero hard statutory conditions have failed. | **More Information Needed (माहिती आवश्यक)** — Missing specific details (e.g., annual income or caste category). |
| `INELIGIBLE` | At least one hard statutory condition (e.g., gender requirement, state domicile, or municipal boundary) evaluates strictly to `False`. | **Not Eligible (अपात्र)** — One or more mandatory conditions are not met. The failed condition is explicitly cited. |
| `NEEDS_REVIEW` | The citizen satisfies the conditions, but the scheme is a candidate under review or lacks non-demo legal approval metadata. | **Under Review (पुनरावलोकन प्रलंबित)** — Scheme criteria undergoing formal legal sign-off. |

---

## 3. AST Structure (`RuleNode`)
Rules are expressed as nested, safe JSON-Logic-like tree structures that reject arbitrary code execution:
- **Logical Nodes**: `all` (logical AND), `any` (logical OR), `not` (logical NOT).
- **Comparison Leaf Nodes**: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `exists`.
- **Statutory Attributes**:
  - `is_hard_statutory`: Boolean flag indicating whether condition failure triggers immediate `INELIGIBLE` status. State residence (`resident_state == "maharashtra"`), gender conditions, and municipal boundaries are automatically treated as hard statutory conditions.
  - `condition_id`: Unique identifier referencing authoritative Government Resolution paragraphs.
  - `as_of_date`: Explicit cut-off date for temporal evaluations (e.g., academic year start or fiscal year end).

---

## 4. Hard Statutory vs. Soft Secondary Criteria
To support intelligent triage, conditions are partitioned:
1. **Hard Statutory Predicates**:
   - Legal Domicile: Resident in Maharashtra (`resident_state == "maharashtra"`).
   - Target Gender: e.g., Majhi Ladki Bahin (`gender == "female"`).
   - Local Body Jurisdiction: e.g., PMC Shahari Garib Arogya requires residence inside Pune Municipal Corporation limits (`municipal_corporation == "mc-pune"`).
   - Social Category: e.g., Post-Matric SC Scholarship (`caste_category in ["SC", "Navbuddha"]`).
   - Failure of any hard condition immediately sets `status = INELIGIBLE` and terminates further requirement probing.
2. **Secondary / Soft Criteria**:
   - Possession of optional certificates (e.g., computer course certificate, sport quota).
   - Bank passbook linkage status (remediable prerequisite).
   - Failure of secondary criteria allows the scheme to be flagged as `PARTIAL` rather than rejected outright.

---

## 5. Production Eligibility Fail-Closed Gate (`check_production_eligibility_gate`)
To prevent provisional development data or demo fixtures from making false eligibility promises to citizens in production, the engine enforces 6 mandatory gates:
1. **Active Rule Status**: `scheme.rule_status == "active"`.
2. **Rejection of Demo Fixtures**: Scheme ID must not start with `demo-`, and `approved_by` must not be `local_demo_fixture_only`.
3. **Untrusted Source Check**: Scheme must not carry `_untrusted_source = True` from unverified external JSON imports.
4. **Trusted Publication Authorization**: `scheme.publication_authorized == True`.
5. **Complete Leaf Evidence**: 100% of leaf nodes in the rule tree must map to validated `RuleEvidence` records with status `LEGAL_APPROVED`.
6. **Temporal Validity**: Current evaluation date must fall strictly within `effective_from <= eval_date <= effective_until`.

If any gate fails, the evaluation status drops to `NEEDS_REVIEW` with an auditable failure note.

---

## 6. Citizen-Explainable Output & Multilingual Breakdowns
Every evaluation response (`EligibilityResult`) returns structured explainability artifacts:
- `matched_conditions`: Human-readable list of satisfied criteria.
- `failed_conditions`: Explicit list of conditions that failed, including exact statutory thresholds (e.g., *"annual_family_income must be at most 250000 (citizen has 300000)"*).
- `unknown_conditions`: Specific fields that need citizen input.
- `condition_tree`: Hierarchical tree of condition evaluations preserving boolean group structure for interactive UI rendering.
- `localized_reason`: Explanations rendered natively in English, Marathi, or Hindi according to citizen preference.

---

## 7. Boundary Testing & Verification
The engine is verified by comprehensive boundary test suites (`test_rule_engine.py`, `test_rule_boundary_matrix.py`, `test_golden_citizen_profiles.py`):
- **Age Boundaries**: Exact evaluation at cut-off dates (e.g., exactly 21st birthday vs. 20 years 364 days for Ladki Bahin).
- **Income Boundaries**: Exactly at threshold (e.g., ₹2,50,000 for EBC fee reimbursement), ₹1 below, and ₹1 above.
- **Disability Percentage**: Exactly 40% (statutory benchmark threshold under RPwD Act, 2016) vs. 39% and 41%.
- **Residency Duration**: Minimum 3 years local municipal residence (tested at 1 year, 3 years, and 5 years).
