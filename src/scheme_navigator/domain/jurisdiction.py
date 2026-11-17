from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class JurisdictionScope(StrEnum):
    CENTRAL = "CENTRAL"
    MAHARASHTRA_STATE = "MAHARASHTRA_STATE"
    DIVISION = "DIVISION"
    DISTRICT = "DISTRICT"
    MUNICIPAL_CORPORATION = "MUNICIPAL_CORPORATION"
    MUNICIPAL_COUNCIL = "MUNICIPAL_COUNCIL"
    NAGAR_PANCHAYAT = "NAGAR_PANCHAYAT"
    GRAM_PANCHAYAT = "GRAM_PANCHAYAT"
    ZILLA_PARISHAD = "ZILLA_PARISHAD"
    WARD = "WARD"
    SPECIAL_AREA = "SPECIAL_AREA"
    CANTONMENT_BOARD = "CANTONMENT_BOARD"


class LocalGovernmentType(StrEnum):
    MUNICIPAL_CORPORATION = "municipal_corporation"
    MUNICIPAL_COUNCIL = "municipal_council"
    NAGAR_PANCHAYAT = "nagar_panchayat"
    GRAM_PANCHAYAT = "gram_panchayat"
    CANTONMENT = "cantonment"


class LocationResolution(BaseModel):
    status: str  # RESOLVED, LOCATION_REQUIRES_CONFIRMATION, UNKNOWN_LOCATION
    state: str = "Maharashtra"
    district: Optional[str] = None
    local_government_type: Optional[str] = None
    local_body_id: Optional[str] = None
    local_body_name_en: Optional[str] = None
    local_body_name_mr: Optional[str] = None
    ward: Optional[str] = None
    pin_code: Optional[str] = None
    applicable_jurisdiction_tokens: list[str] = Field(default_factory=list)
    explanation: str = ""
    candidate_local_bodies: list[str] = Field(default_factory=list)


# Known boundary PIN ambiguities between adjoining local bodies
# When a PIN spans boundaries (e.g. Pune vs PCMC border), explicit confirmation is mandatory
PIN_AMBIGUITY_REGISTRY: dict[str, list[dict[str, str]]] = {
    "411027": [
        {"corporation_id": "mc-pimpri-chinchwad", "name": "Pimpri Chinchwad (Pimple Saudagar / Sangvi)", "district": "Pune"},
        {"corporation_id": "mc-pune", "name": "Pune Municipal Corporation (Aundh Border)", "district": "Pune"}
    ],
    "411061": [
        {"corporation_id": "mc-pimpri-chinchwad", "name": "Pimpri Chinchwad (Dapodi North)", "district": "Pune"},
        {"corporation_id": "mc-pune", "name": "Pune Municipal Corporation (Bopodi / Dapodi South)", "district": "Pune"}
    ],
    "411057": [
        {"corporation_id": "mc-pimpri-chinchwad", "name": "Pimpri Chinchwad (Wakad)", "district": "Pune"},
        {"corporation_id": "mc-pune", "name": "Pune Municipal Corporation (Baner Extension)", "district": "Pune"}
    ],
    "400607": [
        {"corporation_id": "mc-thane", "name": "Thane Municipal Corporation (Ghubunder)", "district": "Thane"},
        {"corporation_id": "mc-mira-bhayander", "name": "Mira Bhayander Municipal Corporation (Kashimira Border)", "district": "Thane"}
    ],
    "410206": [
        {"corporation_id": "mc-panvel", "name": "Panvel Municipal Corporation (New Panvel)", "district": "Raigad"},
        {"corporation_id": "mc-navi-mumbai", "name": "Navi Mumbai Municipal Corporation (Belapur Outskirts)", "district": "Thane"}
    ]
}

# Authoritative Maharashtra 36-District to Administrative Division Mapping
DISTRICT_TO_DIVISION_MAP: dict[str, str] = {
    "mumbai": "Konkan",
    "mumbai city": "Konkan",
    "mumbai suburban": "Konkan",
    "thane": "Konkan",
    "palghar": "Konkan",
    "raigad": "Konkan",
    "ratnagiri": "Konkan",
    "sindhudurg": "Konkan",
    "pune": "Pune",
    "satara": "Pune",
    "sangli": "Pune",
    "solapur": "Pune",
    "kolhapur": "Pune",
    "nashik": "Nashik",
    "dhule": "Nashik",
    "nandurbar": "Nashik",
    "jalgaon": "Nashik",
    "ahilyanagar": "Nashik",
    "ahmednagar": "Nashik",
    "chhatrapati sambhajinagar": "Chhatrapati Sambhajinagar",
    "aurangabad": "Chhatrapati Sambhajinagar",
    "jalna": "Chhatrapati Sambhajinagar",
    "parbhani": "Chhatrapati Sambhajinagar",
    "hingoli": "Chhatrapati Sambhajinagar",
    "nanded": "Chhatrapati Sambhajinagar",
    "beed": "Chhatrapati Sambhajinagar",
    "latur": "Chhatrapati Sambhajinagar",
    "dharashiv": "Chhatrapati Sambhajinagar",
    "osmanabad": "Chhatrapati Sambhajinagar",
    "amravati": "Amravati",
    "akola": "Amravati",
    "yavatmal": "Amravati",
    "buldhana": "Amravati",
    "washim": "Amravati",
    "nagpur": "Nagpur",
    "wardha": "Nagpur",
    "bhandara": "Nagpur",
    "gondia": "Nagpur",
    "chandrapur": "Nagpur",
    "gadchiroli": "Nagpur",
}


class JurisdictionService:
    """Authoritative service for resolving citizen geographic jurisdictions across Maharashtra."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.base_dir = data_dir or (Path(__file__).resolve().parents[3] / "data" / "local_governments")
        self._corporations: dict[str, dict[str, Any]] = {}
        self._ulb_data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        corps_file = self.base_dir / "municipal_corporations.json"
        if corps_file.exists():
            try:
                items = json.loads(corps_file.read_text(encoding="utf-8"))
                for c in items:
                    self._corporations[c["corporation_id"]] = c
            except Exception:
                pass

        ulb_file = self.base_dir / "urban_local_bodies.json"
        if ulb_file.exists():
            try:
                self._ulb_data = json.loads(ulb_file.read_text(encoding="utf-8"))
            except Exception:
                pass

    def list_corporations(self) -> list[dict[str, Any]]:
        return list(self._corporations.values())

    def get_corporation(self, corporation_id: str) -> Optional[dict[str, Any]]:
        return self._corporations.get(corporation_id)

    def get_corporation_by_name(self, name: str) -> Optional[dict[str, Any]]:
        name_lower = name.strip().lower()
        for cid, c in self._corporations.items():
            if (
                cid == name_lower
                or c["official_name_en"].lower() == name_lower
                or c["official_name_mr"].lower() == name_lower
                or any(alias.lower() == name_lower for alias in c.get("official_alternate_names", []))
            ):
                return c
        return None

    def get_wards(self, corporation_id: str) -> Optional[dict[str, Any]]:
        ward_file = self.base_dir / "wards" / f"{corporation_id}.json"
        if ward_file.exists():
            try:
                return json.loads(ward_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        corp = self.get_corporation(corporation_id)
        if corp:
            return {
                "corporation_id": corporation_id,
                "corporation_name_en": corp["official_name_en"],
                "total_wards": corp["ward_count"],
                "representative_wards": corp.get("representative_wards", []),
                "localities": corp.get("locality_directory", [])
            }
        return None

    def get_ulb_data(self) -> dict[str, Any]:
        return self._ulb_data

    def resolve_location(
        self,
        *,
        state: str = "Maharashtra",
        district: Optional[str] = None,
        local_government_type: Optional[str] = None,
        local_body: Optional[str] = None,
        ward: Optional[str] = None,
        pin_code: Optional[str] = None,
    ) -> LocationResolution:
        """Resolve citizen location attributes into a verified LocationResolution."""
        tokens = ["jurisdiction:central"]

        if not state or state.strip().lower() != "maharashtra":
            # Non-Maharashtra resident
            return LocationResolution(
                status="RESOLVED",
                state=state or "Other",
                applicable_jurisdiction_tokens=tokens,
                explanation=f"Citizen is outside Maharashtra. Central schemes apply if resident in India.",
            )

        tokens.append("jurisdiction:state:maharashtra")

        # Check PIN ambiguity first if PIN is supplied
        if pin_code and pin_code.strip() in PIN_AMBIGUITY_REGISTRY:
            ambig_choices = PIN_AMBIGUITY_REGISTRY[pin_code.strip()]
            choice_corps = [c["corporation_id"] for c in ambig_choices]
            
            # If the user has explicitly confirmed their local body matching one of the options, proceed
            matched = None
            if local_body:
                for c in ambig_choices:
                    if local_body.lower() in [c["corporation_id"], c["name"].lower()]:
                        matched = c
                        break
            
            if not matched:
                return LocationResolution(
                    status="LOCATION_REQUIRES_CONFIRMATION",
                    state="Maharashtra",
                    district=district or ambig_choices[0]["district"],
                    pin_code=pin_code.strip(),
                    applicable_jurisdiction_tokens=tokens,
                    explanation=(
                        f"Postal PIN code {pin_code} traverses municipal boundary lines between "
                        f"{' and '.join(c['name'] for c in ambig_choices)}. "
                        f"Please explicitly confirm your municipal corporation or local government body."
                    ),
                    candidate_local_bodies=[c["corporation_id"] for c in ambig_choices]
                )

        # Standard resolution with district and local government
        clean_dist = district.strip().lower() if district else None
        if clean_dist:
            tokens.append(f"jurisdiction:district:{clean_dist}")

        clean_type = local_government_type.strip().lower() if local_government_type else None
        
        # If municipal corporation
        if clean_type in ["municipal_corporation", "corporation"] or (local_body and local_body.startswith("mc-")):
            target_corp = None
            if local_body:
                target_corp = self.get_corporation(local_body) or self.get_corporation_by_name(local_body)
            elif clean_dist and clean_dist in ["pune", "mumbai", "thane", "nagpur", "nashik"]:
                # Ambiguous without specific corporation when district has multiple corporations (e.g. Pune has PMC and PCMC; Thane has TMC, NMMC, KDMC, MBMC, UMC, BNCMC)
                pass

            if target_corp:
                cid = target_corp["corporation_id"]
                tokens.append(f"jurisdiction:mc:{cid}")
                if ward:
                    tokens.append(f"jurisdiction:mc:{cid}:ward:{ward.strip().lower()}")
                return LocationResolution(
                    status="RESOLVED",
                    state="Maharashtra",
                    district=target_corp["district"],
                    local_government_type=LocalGovernmentType.MUNICIPAL_CORPORATION.value,
                    local_body_id=cid,
                    local_body_name_en=target_corp["official_name_en"],
                    local_body_name_mr=target_corp["official_name_mr"],
                    ward=ward,
                    pin_code=pin_code,
                    applicable_jurisdiction_tokens=tokens,
                    explanation=f"Resolved to {target_corp['official_name_en']} ({target_corp['district']} District).",
                )

        # If Municipal Council (Nagar Parishad)
        if clean_type in ["municipal_council", "council", "nagar_parishad"]:
            tokens.append("jurisdiction:tier:municipal_council")
            if local_body:
                tokens.append(f"jurisdiction:council:{local_body.strip().lower()}")
            return LocationResolution(
                status="RESOLVED",
                state="Maharashtra",
                district=district,
                local_government_type=LocalGovernmentType.MUNICIPAL_COUNCIL.value,
                local_body_id=local_body,
                local_body_name_en=f"{local_body} Municipal Council" if local_body else "Municipal Council",
                ward=ward,
                pin_code=pin_code,
                applicable_jurisdiction_tokens=tokens,
                explanation=f"Resolved to Municipal Council tier in {district or 'Maharashtra'}.",
            )

        # If Nagar Panchayat
        if clean_type in ["nagar_panchayat", "panchayat"]:
            tokens.append("jurisdiction:tier:nagar_panchayat")
            if local_body:
                tokens.append(f"jurisdiction:nagar_panchayat:{local_body.strip().lower()}")
            return LocationResolution(
                status="RESOLVED",
                state="Maharashtra",
                district=district,
                local_government_type=LocalGovernmentType.NAGAR_PANCHAYAT.value,
                local_body_id=local_body,
                local_body_name_en=f"{local_body} Nagar Panchayat" if local_body else "Nagar Panchayat",
                ward=ward,
                pin_code=pin_code,
                applicable_jurisdiction_tokens=tokens,
                explanation=f"Resolved to Nagar Panchayat tier in {district or 'Maharashtra'}.",
            )

        # If Rural / Gram Panchayat
        if clean_type in ["gram_panchayat", "rural", "zilla_parishad"]:
            tokens.append("jurisdiction:tier:rural")
            tokens.append("jurisdiction:tier:gram_panchayat")
            if clean_dist:
                tokens.append(f"jurisdiction:zp:{clean_dist}")
            return LocationResolution(
                status="RESOLVED",
                state="Maharashtra",
                district=district,
                local_government_type=LocalGovernmentType.GRAM_PANCHAYAT.value,
                local_body_id=local_body,
                local_body_name_en=f"{local_body} Gram Panchayat" if local_body else "Gram Panchayat",
                ward=ward,
                pin_code=pin_code,
                applicable_jurisdiction_tokens=tokens,
                explanation=f"Resolved to Rural / Gram Panchayat tier under {district or 'District'} Zilla Parishad.",
            )

        # If Cantonment Board (Ministry of Defence, Cantonments Act 2006)
        if clean_type in ["cantonment", "cantonment_board", "cb"]:
            tokens.append("jurisdiction:tier:cantonment")
            if local_body:
                clean_cb = local_body.strip().lower()
                tokens.append(f"jurisdiction:cantonment:{clean_cb}")
            return LocationResolution(
                status="RESOLVED",
                state="Maharashtra",
                district=district,
                local_government_type=LocalGovernmentType.CANTONMENT.value,
                local_body_id=local_body,
                local_body_name_en=f"{local_body} Cantonment Board" if local_body else "Cantonment Board",
                ward=ward,
                pin_code=pin_code,
                applicable_jurisdiction_tokens=tokens,
                explanation=f"Resolved to Cantonment Board (Ministry of Defence) in {district or 'Maharashtra'}.",
            )

        return LocationResolution(
            status="RESOLVED",
            state="Maharashtra",
            district=district,
            applicable_jurisdiction_tokens=tokens,
            explanation=f"Statewide Maharashtra resident scope (District: {district or 'Not specified'}).",
        )

    def is_geographically_applicable(
        self,
        scheme: Any,
        profile: Any,
    ) -> tuple[bool, str]:
        """
        Evaluate statutory geographic compatibility between a Scheme and a CitizenProfile.
        Returns (is_applicable, reason_explanation).
        """
        scope = getattr(scheme, "jurisdiction_scope", "MAHARASHTRA_STATE")
        if hasattr(scope, "value"):
            scope = scope.value
        scope = str(scope).upper()

        # 1. Central Scope
        if scope in ["CENTRAL", "NATIONAL"]:
            # Available nationally
            return True, "Geographically applicable: Central Government scheme open to eligible residents in Maharashtra."

        # 2. Maharashtra State Scope
        resident_state = getattr(profile, "resident_state", None)
        if resident_state and str(resident_state).lower() != "maharashtra":
            return False, f"Geographically inapplicable: Requires legal domicile/residence in Maharashtra (citizen resident in '{resident_state}')."

        if scope in ["MAHARASHTRA_STATE", "STATEWIDE", "STATE"]:
            return True, "Geographically applicable: Statewide Maharashtra programme."

        # 3. District Scope
        if scope in ["DISTRICT", "REGIONAL"]:
            inc_districts = getattr(scheme, "included_local_bodies", []) or []
            target_dist = getattr(scheme, "district_restrictions", None) or []
            all_target_dists = [d.lower() for d in (inc_districts + target_dist)]
            
            p_dist = getattr(profile, "district", None)
            if not p_dist:
                return True, "Geographic applicability pending confirmation of citizen's district."
            
            p_dist_lower = str(p_dist).lower()
            if all_target_dists and not any(p_dist_lower in d or d in p_dist_lower for d in all_target_dists):
                return False, f"Geographically inapplicable: Restricted to districts {all_target_dists} (citizen in '{p_dist}')."
            return True, f"Geographically applicable: District criteria satisfied for {p_dist}."

        # 4. Municipal Corporation Scope
        if scope in ["MUNICIPAL_CORPORATION", "LOCAL_GOVERNMENT"]:
            inc_corps = getattr(scheme, "included_local_bodies", []) or []
            jurisdiction_ids = getattr(scheme, "jurisdiction_ids", []) or []
            all_target_corps = [c.lower() for c in (inc_corps + jurisdiction_ids)]

            p_corp = getattr(profile, "municipal_corporation", None)
            p_type = getattr(profile, "local_government_type", None)

            # If the citizen is confirmed to reside outside a municipal corporation
            if p_type and str(p_type).lower() in ["municipal_council", "nagar_panchayat", "gram_panchayat", "rural", "cantonment", "cantonment_board"]:
                return False, f"Geographically inapplicable: Scheme requires residence inside municipal corporation limits (citizen resides in {p_type})."

            if not p_corp:
                return True, "Geographic applicability pending confirmation of citizen's municipal corporation."

            p_corp_lower = str(p_corp).lower()
            # Match corporation ID or alias
            matched = False
            for target in all_target_corps:
                clean_target = target.replace("jurisdiction:mc:", "").replace("mc-", "").lower()
                clean_p = p_corp_lower.replace("mc-", "").lower()
                if clean_p in clean_target or clean_target in clean_p:
                    matched = True
                    break

            if not matched:
                return False, f"Geographically inapplicable: Programme belongs to {all_target_corps} and does not apply to residents of '{p_corp}'."

            # Check residency duration if required
            req_years = getattr(scheme, "required_residency_years", None)
            if req_years:
                res_years = getattr(profile, "residence_years", None)
                if res_years is not None and res_years < req_years:
                    return False, f"Statutory residency condition failed: Requires at least {req_years} years residence in corporation (citizen has {res_years} years)."

            return True, f"Geographically applicable: Verified resident of {p_corp}."

        # 5. Municipal Council Scope
        if scope in ["MUNICIPAL_COUNCIL", "NAGAR_PARISHAD"]:
            p_corp = getattr(profile, "municipal_corporation", None)
            p_type = getattr(profile, "local_government_type", None)
            if p_corp or (p_type and str(p_type).lower() in ["municipal_corporation", "gram_panchayat", "rural", "cantonment", "cantonment_board"]):
                effective = p_corp or p_type
                return False, f"Geographically inapplicable: Scheme requires residence inside a Municipal Council / Nagar Parishad (citizen resides in '{effective}')."
            return True, "Geographically applicable: Municipal Council tier scheme."

        # 5b. Nagar Panchayat Scope
        if scope == "NAGAR_PANCHAYAT":
            p_corp = getattr(profile, "municipal_corporation", None)
            p_type = getattr(profile, "local_government_type", None)
            if p_corp or (p_type and str(p_type).lower() not in ["nagar_panchayat", "panchayat"]):
                effective = p_corp or p_type
                return False, f"Geographically inapplicable: Scheme requires residence in a Nagar Panchayat (citizen resides in '{effective}')."
            return True, "Geographically applicable: Nagar Panchayat tier scheme."

        # 6. Gram Panchayat / Rural Scope
        if scope in ["GRAM_PANCHAYAT", "RURAL"]:
            p_corp = getattr(profile, "municipal_corporation", None)
            p_type = getattr(profile, "local_government_type", None)
            if p_corp or (p_type and str(p_type).lower() in ["municipal_corporation", "municipal_council", "nagar_panchayat", "cantonment", "cantonment_board"]):
                effective = p_corp or p_type
                return False, f"Geographically inapplicable: Scheme requires residence in a Rural Gram Panchayat jurisdiction (citizen resides in '{effective}')."
            return True, "Geographically applicable: Rural / Gram Panchayat tier scheme."

        # 6b. Zilla Parishad Scope
        if scope in ["ZILLA_PARISHAD", "ZP"]:
            p_corp = getattr(profile, "municipal_corporation", None)
            p_type = getattr(profile, "local_government_type", None)
            if p_corp or (p_type and str(p_type).lower() in ["municipal_corporation", "municipal_council", "cantonment", "cantonment_board"]):
                effective = p_corp or p_type
                return False, f"Geographically inapplicable: Scheme requires residence in rural Zilla Parishad area (citizen resides in '{effective}')."
            return True, "Geographically applicable: Zilla Parishad rural tier scheme."

        # 8. Cantonment Board Scope (Central Ministry of Defence, Cantonments Act 2006)
        if scope in ["CANTONMENT_BOARD", "CANTONMENT"]:
            p_corp = getattr(profile, "municipal_corporation", None)
            p_type = getattr(profile, "local_government_type", None)
            if p_corp or (p_type and str(p_type).lower() not in ["cantonment", "cantonment_board"]):
                effective = p_corp or p_type
                return False, f"Geographically inapplicable: Scheme requires residence within a Cantonment Board area under Ministry of Defence (citizen resides in '{effective}')."

            inc_cbs = getattr(scheme, "included_local_bodies", []) or []
            if inc_cbs:
                p_cb = getattr(profile, "local_body_id", None) or getattr(profile, "cantonment_board", None)
                if not p_cb:
                    return True, "Geographic applicability pending confirmation of citizen's Cantonment Board."
                clean_target_cbs = [c.lower() for c in inc_cbs]
                clean_p_cb = str(p_cb).lower()
                if not any(clean_p_cb in c or c in clean_p_cb for c in clean_target_cbs):
                    return False, f"Geographically inapplicable: Restricted to Cantonment Boards {clean_target_cbs} (citizen in '{p_cb}')."
            return True, "Geographically applicable: Verified Cantonment Board resident."

        # 2b. Administrative Division Scope
        if scope in ["DIVISION", "ADMINISTRATIVE_DIVISION"]:
            inc_divs = getattr(scheme, "included_local_bodies", []) or []
            target_divs = [d.lower() for d in inc_divs]
            p_dist = getattr(profile, "district", None)
            if not p_dist:
                return True, "Geographic applicability pending confirmation of citizen's district."
            
            p_dist_key = str(p_dist).strip().lower()
            p_div = DISTRICT_TO_DIVISION_MAP.get(p_dist_key)
            if p_div and any(t in p_div.lower() or p_div.lower() in t for t in target_divs):
                return True, f"Geographically applicable: Resident of {p_div} Division ({p_dist} District)."
            return False, f"Geographically inapplicable: Restricted to {target_divs} Division (citizen resides in {p_div or 'other'} Division)."

        # 4b. Ward-Level Scope
        if scope == "WARD":
            inc_wards = getattr(scheme, "included_local_bodies", []) or []
            all_target_wards = [w.lower() for w in inc_wards]
            p_ward = getattr(profile, "ward", None)
            p_corp = getattr(profile, "municipal_corporation", None)

            inc_corps = getattr(scheme, "jurisdiction_ids", []) or []
            if p_corp and inc_corps:
                clean_target_corps = [c.replace("jurisdiction:mc:", "").replace("mc-", "").lower() for c in inc_corps]
                clean_p_corp = str(p_corp).replace("mc-", "").lower()
                if not any(clean_p_corp in c or c in clean_p_corp for c in clean_target_corps):
                    return False, f"Geographically inapplicable: Ward scheme belongs to {inc_corps} (citizen in '{p_corp}')."

            if not p_ward:
                return True, "Geographic applicability pending confirmation of citizen's municipal ward."

            clean_p_ward = str(p_ward).strip().lower()
            matched = any(clean_p_ward in w or w in clean_p_ward for w in all_target_wards)
            if not matched:
                return False, f"Geographically inapplicable: Scheme restricted to wards {all_target_wards} (citizen in '{p_ward}')."
            return True, f"Geographically applicable: Verified resident of ward '{p_ward}'."

        # 7. Special Area Scope (e.g. Scheduled Tribal Areas / PESA / Hill Stations)
        if scope == "SPECIAL_AREA":
            inc_areas = getattr(scheme, "included_local_bodies", []) or []
            all_target_areas = [a.lower() for a in inc_areas]
            p_loc = getattr(profile, "locality", None) or getattr(profile, "district", None)
            if not p_loc:
                return True, "Geographic applicability pending confirmation of special designated area."
            clean_loc = str(p_loc).strip().lower()
            if any(a in clean_loc or clean_loc in a for a in all_target_areas):
                return True, f"Geographically applicable: Citizen verified in designated special area '{p_loc}'."
            return False, f"Geographically inapplicable: Scheme restricted to special areas {all_target_areas} (citizen in '{p_loc}')."

        return True, "Geographically applicable."


# Global singleton instance
jurisdiction_service = JurisdictionService()
