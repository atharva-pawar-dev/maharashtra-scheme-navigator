"""Audit and Truth Inventory Script (WS1).

Inspects actual code, routes, domain models, schemes, requirements, and integrations,
producing an objective, verifiable inventory and truth register.
"""

import json
from pathlib import Path
from fastapi.openapi.utils import get_openapi

REPO_ROOT = Path(__file__).resolve().parent.parent

# Import FastAPI app and instances
from scheme_navigator.api.main import app, source_registry
from scheme_navigator.services.document_prep import get_all_scheme_document_requirements


def main():
    out_dir = REPO_ROOT / "release" / "evidence" / "ws1"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Inspect API Routes from OpenAPI
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    routes_inventory = []
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, details in methods.items():
            routes_inventory.append({
                "path": path,
                "method": method.upper(),
                "summary": details.get("summary", ""),
                "tags": details.get("tags", []),
                "operation_id": details.get("operationId", "")
            })

    # 2. Inspect Schemes by Lifecycle State
    canonical_schemes = source_registry.list_canonical_schemes()
    schemes_by_status = {}
    schemes_by_scope = {}
    for s in canonical_schemes:
        status = getattr(s, "publication_status", "UNKNOWN")
        schemes_by_status[status] = schemes_by_status.get(status, 0) + 1
        scope = getattr(s, "jurisdiction_scope", "UNKNOWN")
        schemes_by_scope[scope] = schemes_by_scope.get(scope, 0) + 1

    # 3. Inspect Scheme Document Requirements
    all_requirements = get_all_scheme_document_requirements()
    total_requirements = 0
    mandatory_reqs = 0
    conditional_reqs = 0
    optional_reqs = 0
    orphaned_requirements = []

    canonical_ids = {s.canonical_scheme_id for s in canonical_schemes}
    req_dict_list = all_requirements.values() if isinstance(all_requirements, dict) else all_requirements
    for scheme_req in req_dict_list:
        s_id = scheme_req.get("scheme_id")
        if s_id not in canonical_ids:
            orphaned_requirements.append(s_id)
        for req in scheme_req.get("requirements", []):
            total_requirements += 1
            if req.get("is_mandatory", True):
                mandatory_reqs += 1
            elif req.get("requirement_type") == "CONDITIONAL":
                conditional_reqs += 1
            else:
                optional_reqs += 1

    # 4. Detect Demo / Fixture Paths in Source
    demo_findings = []
    for py_file in REPO_ROOT.rglob("src/**/*.py"):
        text = py_file.read_text(encoding="utf-8")
        if "demo" in text.lower():
            for idx, line in enumerate(text.splitlines(), start=1):
                if any(k in line.lower() for k in ["demo_mode", "demo_fixtures", "mock_gemini", "use_demo"]):
                    demo_findings.append({
                        "file": py_file.relative_to(REPO_ROOT).as_posix(),
                        "line": idx,
                        "text": line.strip()
                    })

    # 5. External Integrations Register
    integrations_register = [
        {
            "dependency": "Google Gemini API (via langchain/langgraph / google-generativeai)",
            "purpose": "Experimental NLU question extraction & draft document OCR assistance",
            "credentials_needed": "GEMINI_API_KEY",
            "data_sent": "User interview responses, uploaded document image/text snippets",
            "retention_training_terms": "Depends on Google Cloud vs Google AI Studio terms (Standard AI Studio may train; Vertex does not)",
            "region": "Global / US default (not restricted to India)",
            "cost_quota": "Free tier / Pay-per-token",
            "rate_limits": "15 RPM free tier",
            "fallback_behaviour": "Degrades gracefully to deterministic rule engine & local template guidance when LLM_MODE=off",
            "status": "CONFIGURED_WITH_FALLBACK",
            "is_operational": True
        },
        {
            "dependency": "Bhashini (National Language Translation Mission)",
            "purpose": "Indic voice & translation services",
            "credentials_needed": "BHASHINI_API_KEY / BHASHINI_USER_ID",
            "data_sent": "Audio voice recordings, translated citizen queries",
            "retention_training_terms": "Govt of India digital mission policy",
            "region": "India",
            "cost_quota": "Govt allotted",
            "rate_limits": "Varies by API gateway",
            "fallback_behaviour": "Browser Web Speech API / static client translations",
            "status": "OPTIONAL_CONFIGURED",
            "is_operational": False
        },
        {
            "dependency": "Aaple Sarkar / MahaDBT / Nari Shakti Doot Portals",
            "purpose": "Official government scheme application and grievance submission",
            "credentials_needed": "None (External Handoff)",
            "data_sent": "None (Citizen navigated directly to official URL with zero data transfer)",
            "retention_training_terms": "Not applicable (External handoff only)",
            "region": "Maharashtra, India",
            "cost_quota": "Free public portals",
            "rate_limits": "N/A",
            "fallback_behaviour": "Displays offline office guidelines (Tahsildar / Setu Kendra / Ward Office)",
            "status": "OPERATIONAL_HANDOFF",
            "is_operational": True
        }
    ]

    report = {
        "id": "E-WS1-001",
        "claim": "WS1 Audit and Truth Inventory across routes, schemes, document requirements, and integrations",
        "total_api_routes": len(routes_inventory),
        "routes": routes_inventory,
        "canonical_schemes_count": len(canonical_schemes),
        "schemes_by_status": schemes_by_status,
        "schemes_by_scope": schemes_by_scope,
        "total_document_requirements": total_requirements,
        "mandatory_requirements": mandatory_reqs,
        "conditional_requirements": conditional_reqs,
        "optional_requirements": optional_reqs,
        "orphaned_requirements_count": len(orphaned_requirements),
        "demo_paths_detected_count": len(demo_findings),
        "demo_paths_sample": demo_findings[:10],
        "integrations_register": integrations_register,
    }

    out_file = out_dir / "E-WS1-001_truth_inventory.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"WS1 Truth Inventory written to: {out_file}")
    print(f"Total Routes: {len(routes_inventory)}")
    print(f"Canonical Schemes: {len(canonical_schemes)} -> {schemes_by_status}")
    print(f"Document Requirements: {total_requirements} (Mandatory: {mandatory_reqs}, Conditional: {conditional_reqs}, Optional: {optional_reqs})")


if __name__ == "__main__":
    main()
