"""Builds the comprehensive 60-scheme Maharashtra Canonical Catalogue."""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

def make_source_ref(source_name, source_url, excerpt, page="Section 1"):
    digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
    return {
        "source_name": source_name,
        "source_url": source_url,
        "source_kind": "official_scheme_page",
        "retrieved_at": "2026-11-13T00:00:00+05:30",
        "page_or_section": page,
        "evidence_excerpt": excerpt,
        "evidence_sha256": digest
    }

def main():
    root = Path(__file__).resolve().parents[1]
    registry_dir = root / "data" / "source_registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    
    # We will load existing canonical_schemes if present to preserve exact citations for candidate schemes
    existing_file = registry_dir / "canonical_schemes.json"
    existing_by_id = {}
    if existing_file.exists():
        for item in json.loads(existing_file.read_text(encoding="utf-8")):
            existing_by_id[item.get("canonical_scheme_id")] = item

    print("Generating comprehensive 60-scheme Maharashtra catalogue...")
    # Import the catalogue definitions module
    from scratch.catalogue_definitions import get_all_60_schemes
    schemes_data = get_all_60_schemes(existing_by_id)

    # 1. Write canonical_schemes.json
    canonical_schemes_list = []
    for s in schemes_data:
        canonical_schemes_list.append(s["canonical_record"])
    
    (registry_dir / "canonical_schemes.json").write_text(
        json.dumps(canonical_schemes_list, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote {len(canonical_schemes_list)} canonical schemes to {registry_dir / 'canonical_schemes.json'}")

    # 2. Write application_channels.json
    channels_list = []
    for s in schemes_data:
        channels_list.append(s["channel_record"])
    (registry_dir / "application_channels.json").write_text(
        json.dumps(channels_list, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote {len(channels_list)} application channels to {registry_dir / 'application_channels.json'}")

    # 3. Write data/demo/schemes.json so catalog.all() serves all 60 schemes to Explore Schemes and Find Schemes
    demo_schemes_list = []
    for s in schemes_data:
        demo_schemes_list.append(s["runtime_scheme"])
    
    demo_schemes_file = root / "data" / "demo" / "schemes.json"
    demo_schemes_file.parent.mkdir(parents=True, exist_ok=True)
    demo_schemes_file.write_text(
        json.dumps(demo_schemes_list, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Wrote {len(demo_schemes_list)} runtime schemes to {demo_schemes_file}")

if __name__ == "__main__":
    main()
