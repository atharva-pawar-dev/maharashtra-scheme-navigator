# Maharashtra Canonical Scheme Reconciliation (docs/catalogue/canonical_scheme_reconciliation.md)
**Snapshot:** `U-20261120`  
**Standard:** TRIMURTI v3 Invariant I-12 (Non-Destructive Data Evolution) & Section 18  
**Total Reconciled Records:** 74 Canonical + 1 Quarantined Demo Fixture = 75  

## 1. Candidate Disposition Summary
- **Total Candidates Discovered**: 75
- **In Catalogue Verified (Tier A)**: 17 (100% verified verbatim quotes, substantive criteria >= 2)
- **In Catalogue Secondary / Municipal (Tier B)**: 13 (PMC, PCMC, BMC, TMC, NMMC)
- **In Catalogue Exploratory (Tier C)**: 44 (Discovered, limited-info matching, quarantined by Thin-Rule Protection)
- **Quarantined Demo Fixtures**: 1 (`demo-majhi-ladki-bahin`)

## 2. Canonical Compatibility Alias Mappings
- `MHA-S-0001` -> `candidate-sanjay-gandhi-niradhar-anudan`
- `MHA-S-0002` -> `demo-indira-gandhi-old-age-pension`
- `MHA-S-0003` -> `candidate-majhi-ladki-bahin`
- `MHA-S-0004` -> `candidate-punjabrao-deshmukh-hostel`
- `MHA-S-0005` -> `scheme-ebc-tuition-waiver`
- `MHA-S-0006` -> `scheme-namo-shetkari-maha-samman`
- `MHA-S-0007` -> `scheme-mjpjay-ayushman-bharat`
- `MHA-S-0008` -> `candidate-savitribai-phule-scholarship`
- `MHA-S-0009` -> `scheme-mukhyamantri-vayoshri`
- `MHA-S-0010` -> `scheme-swadhar-yojana`
- `MHA-S-0011` -> `scheme-babu-jagjivan-ram-chhatrawas`
- `MHA-S-0012` -> `scheme-eklavya-scholarship`
- `scheme-ignoaps` -> `demo-indira-gandhi-old-age-pension`
- `scheme-cmegp-maharashtra` -> `scheme-cmegp-self-employment`
- `scheme-annasaheb-patil-loan` -> `scheme-annasaheb-patil-ir2`

## 3. Quarantined Demo Data Isolation
Under Invariant I-04, `demo-majhi-ladki-bahin` is explicitly marked `publication_authorized=False` and `rule_status='draft'`. It is rejected by `check_production_eligibility_gate` and fails closed with message: *'This rule is a demo fixture or lacks non-demo approval metadata. Eligibility cannot be confirmed.'*
