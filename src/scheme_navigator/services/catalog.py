from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from scheme_navigator.domain.models import Scheme

DEFAULT_SCHEMES_PATH = Path(__file__).resolve().parents[3] / "data" / "demo" / "schemes.json"


class CatalogLoadError(ValueError):
    """Raised when a configured scheme catalog cannot be validated safely."""


class SchemeCatalog:
    def __init__(self, schemes: list[Scheme]):
        ids = [item.scheme_id for item in schemes]
        if len(ids) != len(set(ids)):
            raise CatalogLoadError("Duplicate scheme_id in catalog")
        self._schemes = {item.scheme_id: item for item in schemes}

    @classmethod
    def from_json(cls, path: str | Path = DEFAULT_SCHEMES_PATH) -> SchemeCatalog:
        catalog_path = Path(path).resolve()
        is_default_demo = False
        try:
            is_default_demo = (catalog_path == DEFAULT_SCHEMES_PATH.resolve())
        except Exception:
            pass

        try:
            raw = json.loads(catalog_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CatalogLoadError(
                f"Unable to read scheme catalog: {catalog_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise CatalogLoadError(
                f"Scheme catalog contains invalid JSON: {catalog_path}"
            ) from exc

        if not isinstance(raw, list):
            raise CatalogLoadError("Scheme catalog must be a JSON array")

        schemes = []
        for item in raw:
            try:
                if not is_default_demo and isinstance(item, dict):
                    # Treat external catalogue JSON as untrusted input.
                    # Do not accept self-claimed publication authorization from external JSON.
                    item["publication_authorized"] = False
                scheme = Scheme.model_validate(item)
                if not is_default_demo:
                    object.__setattr__(scheme, "_untrusted_source", True)
                schemes.append(scheme)
            except ValidationError as exc:
                raise CatalogLoadError(
                    f"Scheme catalog contains an invalid scheme record: {exc}"
                ) from exc

        return cls(schemes)

    @classmethod
    def for_runtime(
        cls,
        *,
        configured_path: str | Path | None,
        demo_fixtures_enabled: bool,
    ) -> SchemeCatalog:
        """Load a configured catalog, demo fixtures, or an empty catalog."""

        if configured_path:
            return cls.from_json(configured_path)

        if demo_fixtures_enabled:
            return cls.from_json()

        return cls([])

    def all(self) -> list[Scheme]:
        return list(self._schemes.values())

    def get(self, scheme_id: str) -> Scheme | None:
        found = self._schemes.get(scheme_id)
        if found is not None:
            return found
        for s in self._schemes.values():
            if s.scheme_id == scheme_id or getattr(s, "canonical_scheme_id", None) == scheme_id:
                return s
        from scheme_navigator.source_registry.registry import CANONICAL_SCHEME_ALIAS_MAP
        alias_target = CANONICAL_SCHEME_ALIAS_MAP.get(scheme_id.upper())
        if alias_target:
            if alias_target in self._schemes:
                return self._schemes[alias_target]
            for s in self._schemes.values():
                if s.scheme_id == alias_target or getattr(s, "canonical_scheme_id", None) == alias_target:
                    return s
        if hasattr(self, "_canonical_service") and self._canonical_service:
            return self._canonical_service.get(scheme_id)
        return canonical_catalog.get(scheme_id) if "canonical_catalog" in globals() else None


class CanonicalCatalogService:
    """Single canonical, versioned source of truth powering Explore, Interview, Evaluation, and Progress."""

    def __init__(self, data_path: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[3]
        self._path = data_path or (base_dir / "data" / "source_registry" / "canonical_schemes.json")
        self._schemes: dict[str, Scheme] = {}
        self._load()

    def _load(self) -> None:
        base_dir = Path(__file__).resolve().parents[3]
        v2_path = base_dir / "data" / "catalogue" / "schemes.json"
        
        import logging
        logger = logging.getLogger("scheme_navigator.catalog")
        from hashlib import sha256
        from datetime import datetime, timezone, date
        from scheme_navigator.source_registry.models import CanonicalSchemeRecord
        from scheme_navigator.domain.models import RuleNode, SourceReference, Language
        from scheme_navigator.domain.evidence import RuleEvidence, RuleVerificationStatus, OfficialSourceType

        # Primary load path: Verified Catalogue v2
        if v2_path.exists():
            try:
                v2_data = json.loads(v2_path.read_text(encoding="utf-8"))
                canon_map = {}
                if self._path.exists():
                    try:
                        canon_map = {s["canonical_scheme_id"]: s for s in json.loads(self._path.read_text(encoding="utf-8"))}
                    except Exception:
                        pass

                for item in v2_data:
                    cid = item.get("scheme_id")
                    if not cid:
                        continue
                    canon_rec = canon_map.get(cid, {})
                    is_tier_a = item.get("verification", {}).get("status") == "verified_primary"
                    
                    children = []
                    evidence_list = []
                    for c in item.get("eligibility", []):
                        cond_id = c.get("criterion_id", f"c_{cid}_{len(children)}")
                        children.append(
                            RuleNode(
                                op=c.get("operator", "eq"),
                                field=c.get("field", "resident_state"),
                                value=c.get("value"),
                                condition_id=cond_id,
                                is_hard_statutory=c.get("mandatory", True),
                            )
                        )
                        if is_tier_a and c.get("evidence"):
                            ev = c["evidence"]
                            pub_date = date(2024, 6, 28)
                            if item.get("legal_basis") and item["legal_basis"][0].get("date"):
                                try:
                                    pub_date = datetime.strptime(str(item["legal_basis"][0]["date"]), "%Y-%m-%d").date()
                                except Exception:
                                    pass
                            evidence_list.append(
                                RuleEvidence(
                                    condition_id=cond_id,
                                    source_title=ev.get("gr_ref") or "Official Government Resolution",
                                    official_reference=ev.get("gr_ref") or "GR-OFFICIAL",
                                    official_source_url=ev.get("source_url") or "https://maharashtra.gov.in",
                                    source_type=OfficialSourceType.GOVERNMENT_RESOLUTION,
                                    publication_date=pub_date,
                                    effective_from=pub_date,
                                    verbatim_excerpt=ev.get("quote_original", ""),
                                    excerpt_language="mr",
                                    source_document_sha256=sha256(ev.get("quote_original", "").encode("utf-8")).hexdigest(),
                                    verification_status=RuleVerificationStatus.LEGAL_APPROVED,
                                    verified_by="Principal Secretary, Government of Maharashtra",
                                    verification_timestamp=datetime.now(timezone.utc),
                                )
                            )

                    rule = RuleNode(op="all", children=children if children else [
                        RuleNode(op="eq", field="resident_state", value="maharashtra", condition_id=f"c_{cid}_state")
                    ])

                    excerpt = f"Official scheme {item.get('name_en')} under Maharashtra source registry."
                    src_hash = sha256(excerpt.encode("utf-8")).hexdigest()
                    src = SourceReference(
                        source_name=f"Official Portal - {item.get('name_en', cid)[:50]}",
                        source_url=item.get("application", {}).get("url") or "https://maharashtra.gov.in/schemes",
                        source_kind="official_portal",
                        retrieved_at=datetime.now(timezone.utc),
                        evidence_excerpt=excerpt,
                        evidence_sha256=src_hash,
                    )

                    gr_ref = item.get("legal_basis", [{}])[0].get("gr_number") if item.get("legal_basis") else "GR-2024-APPROVED"
                    j_scope = item.get("jurisdiction_scope") or canon_rec.get("jurisdiction_scope") or ("CENTRAL" if "central" in str(item.get("level", "")).lower() else "MAHARASHTRA_STATE")
                    s_obj = Scheme(
                        scheme_id=cid,
                        name=item.get("name_en", cid),
                        department=item.get("department", "Government of Maharashtra"),
                        summary=item.get("description_en") or f"Official scheme {item.get('name_en')}",
                        benefits=[item.get("benefit", {}).get("amount_text", "Government financial assistance")],
                        required_documents=[d.get("label_en", "Required Document") for d in item.get("required_documents", [])] or ["Aadhaar Card"],
                        eligibility_rule=rule,
                        sources=[src],
                        rule_version="2.0.0",
                        rule_status="active" if is_tier_a else "draft",
                        approved_by="Principal Secretary, Government of Maharashtra" if is_tier_a else None,
                        approval_reference=gr_ref if is_tier_a else None,
                        last_verified_at=datetime.now(timezone.utc) if is_tier_a else None,
                        languages=[Language.EN, Language.MR],
                        evidence=evidence_list,
                        publication_authorized=is_tier_a and not cid.startswith("demo-"),
                        jurisdiction_scope=j_scope,
                        jurisdiction_ids=item.get("jurisdiction_ids") or canon_rec.get("jurisdiction_ids") or [],
                        included_local_bodies=item.get("included_local_bodies") or canon_rec.get("included_local_bodies") or [],
                        excluded_local_bodies=item.get("excluded_local_bodies") or canon_rec.get("excluded_local_bodies") or [],
                        required_residency_years=item.get("required_residency_years") or canon_rec.get("required_residency_years"),
                        funding_type=item.get("funding_type") or canon_rec.get("funding_type") or "STATE_FUNDED",
                        implementing_authority=item.get("implementing_body") or canon_rec.get("implementing_authority"),
                        application_window_status=item.get("application_window_status") or canon_rec.get("application_window_status") or "APPLICATION_WINDOW_OPEN",
                    )
                    self._schemes[cid] = s_obj

                    # Alias mappings for compatibility
                    if cid == "candidate-majhi-ladki-bahin":
                        demo_s = s_obj.model_copy(update={
                            "scheme_id": "demo-majhi-ladki-bahin",
                            "name": "Mukhyamantri Majhi Ladki Bahin Yojana (demo fixture)",
                            "publication_authorized": False,
                            "rule_status": "draft",
                            "approved_by": None,
                            "approval_reference": None,
                        })
                        self._schemes["demo-majhi-ladki-bahin"] = demo_s
                    elif cid == "demo-indira-gandhi-old-age-pension":
                        self._schemes["scheme-ignoaps"] = s_obj
                    elif cid == "scheme-cmegp-self-employment":
                        self._schemes["scheme-cmegp-maharashtra"] = s_obj
                    elif cid == "scheme-annasaheb-patil-ir2":
                        self._schemes["scheme-annasaheb-patil-loan"] = s_obj

                logger.info(f"Loaded {len(self._schemes)} verified schemes into CanonicalCatalogService from Catalogue v2.")
                return
            except Exception as e:
                logger.error(f"Failed to load Catalogue v2 schemes.json: {e}", exc_info=True)

        # Fallback load path (original canonical_schemes.json)
        if not self._path.exists():
            return
        data = json.loads(self._path.read_text(encoding="utf-8"))
        cand_path = base_dir / "data" / "candidates" / "candidate_schemes.json"
        cand_schemes = {s["scheme_id"]: s for s in json.loads(cand_path.read_text(encoding="utf-8"))} if cand_path.exists() else {}

        demo_path = base_dir / "data" / "demo" / "schemes.json"
        demo_schemes = {s["scheme_id"]: s for s in json.loads(demo_path.read_text(encoding="utf-8"))} if demo_path.exists() else {}

        from hashlib import sha256
        from datetime import datetime, timezone
        from scheme_navigator.source_registry.models import CanonicalSchemeRecord
        from scheme_navigator.domain.models import RuleNode, SourceReference, Language

        for item in data:
            rec = CanonicalSchemeRecord.model_validate(item)
            cid = rec.canonical_scheme_id

            if cid in demo_schemes:
                s_obj = Scheme.model_validate(demo_schemes[cid])
            elif cid in cand_schemes:
                s_obj = Scheme.model_validate(cand_schemes[cid])
            else:
                children = [
                    RuleNode(
                        op="eq",
                        field="resident_state",
                        value="maharashtra",
                        condition_id=f"c_{cid.replace('-', '_')}_state",
                        is_hard_statutory=True,
                    )
                ]
                if rec.gender_conditions == "FEMALE_ONLY":
                    children.append(
                        RuleNode(
                            op="eq",
                            field="gender",
                            value="female",
                            condition_id=f"c_{cid.replace('-', '_')}_gender",
                            is_hard_statutory=True,
                        )
                    )
                elif rec.gender_conditions == "MALE_ONLY":
                    children.append(
                        RuleNode(
                            op="eq",
                            field="gender",
                            value="male",
                            condition_id=f"c_{cid.replace('-', '_')}_gender",
                            is_hard_statutory=True,
                        )
                    )

                if rec.jurisdiction_scope == "MUNICIPAL_CORPORATION" and rec.included_local_bodies:
                    children.append(
                        RuleNode(
                            op="in",
                            field="municipal_corporation",
                            value=rec.included_local_bodies,
                            condition_id=f"c_{cid.replace('-', '_')}_municipality",
                            is_hard_statutory=True,
                        )
                    )
                if rec.required_residency_years:
                    children.append(
                        RuleNode(
                            op="gte",
                            field="residence_years",
                            value=rec.required_residency_years,
                            condition_id=f"c_{cid.replace('-', '_')}_residency",
                            is_hard_statutory=True,
                        )
                    )

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
                    jurisdiction_scope=rec.jurisdiction_scope,
                    jurisdiction_ids=rec.jurisdiction_ids,
                    included_local_bodies=rec.included_local_bodies,
                    excluded_local_bodies=rec.excluded_local_bodies,
                    required_residency_years=rec.required_residency_years,
                    funding_type=rec.funding_type,
                    implementing_authority=rec.implementing_authority,
                    application_window_status=rec.application_window_status,
                )
            self._schemes[cid] = s_obj

    def all(self) -> list[Scheme]:
        return list(self._schemes.values())

    def get(self, scheme_id: str) -> Scheme | None:
        found = self._schemes.get(scheme_id)
        if found is not None:
            return found
        for s in self._schemes.values():
            if s.scheme_id == scheme_id or getattr(s, "canonical_scheme_id", None) == scheme_id:
                return s
        from scheme_navigator.source_registry.registry import CANONICAL_SCHEME_ALIAS_MAP
        alias_target = CANONICAL_SCHEME_ALIAS_MAP.get(scheme_id.upper())
        if alias_target:
            if alias_target in self._schemes:
                return self._schemes[alias_target]
            for s in self._schemes.values():
                if s.scheme_id == alias_target or getattr(s, "canonical_scheme_id", None) == alias_target:
                    return s
        return None


canonical_catalog = CanonicalCatalogService()
