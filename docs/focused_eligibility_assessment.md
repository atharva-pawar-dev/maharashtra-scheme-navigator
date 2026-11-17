# Focused Eligibility Assessment: Single-Scheme Targeted Evaluation

## 1. Overview and Problem Definition

In earlier iterations of Scheme Navigator, clicking *Check Eligibility* for a specific scheme (e.g. *Mukhyamantri Majhi Ladki Bahin Yojana*) transferred the citizen to the general interview flow. Because the agent evaluated entropy across the entire 60-scheme catalogue, it asked questions about irrelevant criteria (such as whether the applicant is a student, their landholding hectares, or their caste category) that had zero bearing on the selected scheme. Furthermore, the subsequent results view displayed all 60 schemes rather than the scheme the citizen had chosen to assess.

The **Focused Eligibility Assessment** engine solves this completely.

---

## 2. Targeted Question Selection Algorithm

In `src/scheme_navigator/agents/interviewer.py`:

```python
# In FOCUSED_SCHEME mode, restrict candidate schemes strictly to target scheme
if (mode == "FOCUSED_SCHEME" or target_scheme_id) and target_scheme_id:
    focused = [s for s in schemes if s.scheme_id == target_scheme_id]
    if focused:
        schemes = focused
```

1. **Candidate Restriction**: The candidate schemes list is narrowed from 60 schemes down to strictly the single `target_scheme`.
2. **Missing Criterion Direct Priority**:
   ```python
   if mode == "FOCUSED_SCHEME" or target_scheme_id:
       candidates.append((1.0, slot))
   ```
   Only criteria present in the target scheme's AST rule (e.g., gender, residence, age, income, and Aadhaar bank account for Ladki Bahin) are considered.
3. **Zero Extraneous Questions**: Unrelated slots (e.g. student status, disability, land ownership) have 0 presence in the rule AST and are never asked.
4. **Instant Evaluation on Complete Profile**: If the citizen's persistent profile already satisfies all required criteria for the target scheme, `_choose_question` returns `is_complete=True` immediately without asking redundant questions.

---

## 3. Dedicated Focused Result View

When navigating to `/results` in `FOCUSED_SCHEME` mode:

1. **Scoreboard Elimination**: The 5-outcome catalogue scoreboard (`.scoreboard`) is hidden (`display: none`).
2. **Accordion Elimination**: The collapsed rejected schemes accordion (`#not-eligible-accordion`) is hidden (`display: none`).
3. **Contextual Headers**:
   - Title: *Focused Scheme Eligibility Assessment* / *विशिष्ट योजना पात्रता निकाल*
   - Subtitle: *Eligibility assessment result for your selected scheme based on verified statutory rules.*
4. **Focused Scheme Card Details**:
   - Status Badge: Clear semantic status (*Eligible*, *Partial Match*, *Needs Information*, *Not Eligible*, or *Caseworker Review*).
   - Scheme Name & Verified Code.
   - Statutory Reason: Explaining why the citizen qualifies or does not qualify according to the Government Resolution.
   - Satisfied Criteria Pills: `✓ [Criterion]` in green.
   - Unmet Criteria Pills: `✗ [Criterion]` in red.
   - Missing Information Pills: `? [Criterion]` in amber.
   - Verified Official Sources: Direct clickable links and citations to Government Resolutions (GRs) and official departmental portals.
   - Direct CTA:
     - If Eligible: *Begin application preparation →* (activates scheme progress and opens workspace).
     - If Ineligible / Missing: *Find Other Schemes* or *Answer questions to check eligibility*.
