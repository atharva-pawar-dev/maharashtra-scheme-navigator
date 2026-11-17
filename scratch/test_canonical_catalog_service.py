import json
from pathlib import Path
from scheme_navigator.source_registry.registry import SourceRegistry
from scheme_navigator.source_registry.models import CanonicalSchemeRecord
from scheme_navigator.domain.models import Scheme, RuleNode, SourceReference, Language
from datetime import datetime, timezone

class CanonicalCatalogService:
    def __init__(self, data_path: Path | None = None):
        base_dir = Path(__file__).resolve().parents[1]
        self._path = data_path or (base_dir / "data" / "source_registry" / "canonical_schemes.json")
        self._schemes: dict[str, Scheme] = {}
        self._load()

    def _load(self):
        base_dir = Path(__file__).resolve().parents[1]
        data = json.loads(self._path.read_text(encoding="utf-8"))
        cand_path = base_dir / "data" / "candidates" / "candidate_schemes.json"
        cand_schemes = {s["scheme_id"]: s for s in json.loads(cand_path.read_text(encoding="utf-8"))} if cand_path.exists() else {}

        demo_path = base_dir / "data" / "demo" / "schemes.json"
        demo_schemes = {s["scheme_id"]: s for s in json.loads(demo_path.read_text(encoding="utf-8"))} if demo_path.exists() else {}

        from hashlib import sha256

        for item in data:
            rec = CanonicalSchemeRecord.model_validate(item)
            cid = rec.canonical_scheme_id

            if cid in demo_schemes:
                s_obj = Scheme.model_validate(demo_schemes[cid])
            elif cid in cand_schemes:
                s_obj = Scheme.model_validate(cand_schemes[cid])
            else:
                children = [
                    RuleNode(op="eq", field="resident_state", value="maharashtra", condition_id=f"c_{cid.replace('-', '_')}_state")
                ]
                if rec.gender_conditions == "FEMALE_ONLY":
                    children.append(RuleNode(op="eq", field="gender", value="female", condition_id=f"c_{cid.replace('-', '_')}_gender"))
                elif rec.gender_conditions == "MALE_ONLY":
                    children.append(RuleNode(op="eq", field="gender", value="male", condition_id=f"c_{cid.replace('-', '_')}_gender"))

                excerpt = f"Official scheme {rec.official_scheme_name} registered under Government of Maharashtra source registry."
                src_hash = sha256(excerpt.encode("utf-8")).hexdigest()

                src = SourceReference(
                    source_name=f"Official Portal - {rec.official_scheme_name[:50]}",
                    source_url="https://maharashtra.gov.in/schemes",
                    source_kind="official_portal",
                    retrieved_at=datetime.now(timezone.utc),
                    evidence_excerpt=excerpt,
                    evidence_sha256=src_hash,
                )

                rule = RuleNode(op="all", children=children)
                s_obj = Scheme(
                    scheme_id=cid,
                    name=rec.official_scheme_name,
                    department=rec.responsible_department,
                    summary=rec.scheme_objective or f"Official scheme {rec.official_scheme_name}",
                    benefits=[rec.benefit_description or rec.benefit_amount or "Government financial assistance"],
                    required_documents=rec.required_documents or ["Aadhaar Card"],
                    eligibility_rule=rule,
                    sources=[src],
                    rule_version=rec.rule_version or "1.0.0",
                    rule_status="draft",
                    publication_authorized=False,
                )
            self._schemes[cid] = s_obj

    def all(self) -> list[Scheme]:
        return list(self._schemes.values())

    def get(self, scheme_id: str) -> Scheme | None:
        return self._schemes.get(scheme_id)

service = CanonicalCatalogService()
print(f"Service loaded {len(service.all())} schemes.")
p1 = service.get("scheme-pm-kisan")
print("PM Kisan retrieved:", p1.name if p1 else "None")
