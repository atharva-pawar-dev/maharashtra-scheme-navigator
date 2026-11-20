from scheme_navigator.services.catalog import canonical_catalog
from scheme_navigator.governance.attestation_store import attestation_store, compute_scheme_rule_set_hash
from scheme_navigator.governance.thin_rule_lint import lint_scheme_rules

schemes = canonical_catalog.all()
print(f"Total schemes in canonical_catalog: {len(schemes)}")

attested = 0
thin = 0
for s in schemes:
    rule_hash = compute_scheme_rule_set_hash(s)
    att = attestation_store.get_valid_attestation(s.scheme_id, rule_hash)
    lint = lint_scheme_rules(s)
    if att:
        attested += 1
        print(f"ATTESTED: {s.scheme_id} | Lint valid: {lint.is_valid} | Substantive: {lint.substantive_criteria_count}")
    elif not lint.is_valid:
        thin += 1

print(f"\nSummary: Attested={attested}, Thin/Unattested={thin}, Total={len(schemes)}")
