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
        return None


canonical_catalog = CanonicalCatalogService()
