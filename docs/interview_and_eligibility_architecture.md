# Maharashtra Scheme Navigator: Interview and Eligibility Architecture

## Executive Summary
This document delineates the technical architecture of the adaptive citizen interview and deterministic eligibility evaluation engine powering the **Maharashtra Scheme Navigator**. In contrast to probabilistic LLM judgments, the Scheme Navigator employs a deterministic, rule-based inference engine that executes formal statutory conditions derived from official Government Resolutions (GRs).

---

## 1. Adaptive Interview System
The interview journey operates on an adaptive questionnaire model implemented via LangGraph workflows and FastAPI backend endpoints (`/interview/start`, `/interview/answer`).

### A. Dual Assessment Modes
1. **Global Exploration Journey (`scope="canonical"`)**:
   - Asks progressive demographic and socio-economic questions (domicile, age, gender, caste, income, disability, student status, landholding, ration card).
   - Dynamically selects the next question that maximizes entropy reduction across all 60 canonical schemes.
2. **Focused Single-Scheme Assessment (`scheme_id="SCHEME-MH-..."`)**:
   - Triggered when a citizen clicks "Check My Eligibility" (`माझी पात्रता तपासा`) directly on a scheme card in Explore or Results.
   - Questions are scoped strictly to the missing conditions for the designated scheme, avoiding extraneous questions and expediting the citizen's journey.

### B. Live Profile Sidebar Synchronization
Throughout the interview, every citizen response updates the unified `CitizenProfile` state. The frontend sidebar (`.interview-sidebar`) reactively displays:
- Complete key-value pairs (State, Gender, Age, Annual Income, Category, Student Status, BPL, Landholding, Disability %, Marital Status, Ration Card).
- Visual Progress Meter (`#profile-meter-bar`) calculating percentage completeness across the 11 canonical profile attributes.
- "Evaluate Schemes Now" button (`#btn-evaluate-now`) allowing early exit to view tentative results once basic criteria are provided.

---

## 2. Deterministic 5-Outcome Eligibility Engine
The core rule engine (`src/scheme_navigator/services/rule_engine.py`) evaluates candidate schemes against a `CitizenProfile` using formal Boolean propositional logic.

### The Five Invariant Outcomes
1. **`ELIGIBLE` (`पात्र`)**:
   - All statutory hard and soft rules evaluate to `True`.
   - The scheme has verified legal publication approval.
   - The citizen is invited to begin application preparation with the primary CTA (`अर्ज तयारी सुरू करा →`).
2. **`PARTIAL` (`अंशतः पात्र`)**:
   - The citizen satisfies all statutory hard conditions (e.g., domicile, age boundaries, statutory income caps).
   - The citizen satisfies at least 70% of total conditions (`pass_ratio >= 0.70`).
   - At most 2 non-hard conditions are failed (e.g., secondary documentation or minor criteria).
   - Displayed in the Partial Match Scoreboard with the secondary CTA "See how to qualify" (`पात्र कसे व्हावे ते पहा`).
3. **`NEEDS_INFO` (`अधिक माहिती आवश्यक`)**:
   - Zero hard conditions failed, but one or more critical attributes remain unknown (`None`).
   - Displayed in the Information Needed Scoreboard with CTA "Answer questions to check eligibility" (`पात्रतेसाठी उत्तर द्या`).
4. **`NEEDS_REVIEW` (`समीक्षक पुनरावलोकन`)**:
   - The scheme is unverified, marked as a demo fixture (`LOCAL_DEMO_FIXTURE_ONLY`), or requires mandatory caseworker discretion under the Maharashtra Right to Public Services Act (RTS 2015).
   - Fails-closed so unverified or unapproved schemes are never certified as `ELIGIBLE`.
5. **`INELIGIBLE` (`सध्याच्या माहितीनुसार अपात्र`)**:
   - One or more statutory hard rules fail (e.g., annual income exceeds cap, citizen resides outside Maharashtra, age is outside statutory window).
   - Grouped into a dedicated collapsed accordion (`<details id="not-eligible-accordion">`), displaying transparently which specific conditions failed without cluttering the eligible results.

---

## 3. Statutory Hard Rules vs. Soft Conditions
The engine classifies rule conditions via the `RuleNode.is_hard_statutory` attribute:

```python
HARD_STATUTORY_FIELDS = {
    "resident_state",       # Non-negotiable Maharashtra domicile
    "annual_family_income", # Legal upper income ceiling
    "age", "age_years",     # Statutory age limits
    "gender",               # Targeted gender criteria (e.g., Majhi Ladki Bahin)
    "caste_category",       # Constitutional caste reservation categories
    "bpl",                  # Below Poverty Line requirement
    "ration_card_type",     # Food security entitlement category
}
```

### Statutory Fail-Closed Invariant
If **any** condition referencing a hard statutory field fails:
- The scheme is immediately classified as `INELIGIBLE`.
- The rule engine short-circuits: a candidate scheme with a failed statutory hard condition can **never** be classified as `PARTIAL` or `ELIGIBLE`, regardless of how many other rules passed.

---

## 4. Partial Matching Calculation
For candidate schemes where no hard conditions failed, the engine evaluates soft rules:
$$\text{pass\_ratio} = \frac{\text{count}(\text{matched\_conditions})}{\text{count}(\text{matched\_conditions}) + \text{count}(\text{failed\_conditions}) + \text{count}(\text{unknown\_conditions})}$$

A scheme qualifies for `PARTIAL` status if and only if:
1. $\text{count}(\text{failed\_hard\_conditions}) == 0$
2. $\text{pass\_ratio} \ge 0.70$
3. $\text{count}(\text{failed\_conditions}) \le 2$

---

## 5. Result Verification
The implementation is verified by comprehensive golden profile suites (`tests/test_golden_citizen_profiles.py`), scoped assessment tests (`tests/test_focused_assessment_and_progress.py`), and end-to-end browser tests (`tests/test_browser_citizen_experience.py`).
