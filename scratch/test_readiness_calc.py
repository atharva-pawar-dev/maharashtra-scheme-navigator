from scheme_navigator.source_registry.models import CanonicalSchemeRecord
from scheme_navigator.source_registry.registry import SourceRegistry
from scheme_navigator.governance.attestation_store import attestation_store, compute_scheme_rule_set_hash
from scheme_navigator.governance.thin_rule_lint import lint_scheme_rules
from scheme_navigator.services.catalog import canonical_catalog

reg = SourceRegistry()
schemes = reg.list_canonical_schemes()
print(f"Total schemes in registry: {len(schemes)}")

ready = 0
limited = 0
demo = 0
for s in schemes:
    scheme_domain = canonical_catalog.get(s.canonical_scheme_id)
    if s.canonical_scheme_id.startswith("demo-"):
        demo += 1
    elif scheme_domain:
        rule_hash = compute_scheme_rule_set_hash(scheme_domain)
        att = attestation_store.get_valid_attestation(scheme_domain.scheme_id, rule_hash)
        lint = lint_scheme_rules(scheme_domain)
        if att and lint.is_valid:
            ready += 1
        else:
            limited += 1
    else:
        limited += 1

print(f"Decision Ready: {ready}, Limited Information: {limited}, Demo: {demo}")
