from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from scheme_navigator.domain.models import SourceReference
from scheme_navigator.ingestion.pipeline import ingest_public_source
from scheme_navigator.llm.compiler import compile_gr_text_offline


def main() -> None:
    parser = argparse.ArgumentParser(prog="scheme-navigator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Fetch one allowlisted HTTPS government source")
    ingest.add_argument("url")
    ingest.add_argument("--output-dir", default="data/ingested")
    ingest.add_argument("--ignore-robots", action="store_true", help="Not recommended; manual source-policy exception only")

    compile_parser = subparsers.add_parser("compile-rule", help="Compile a draft rule with the local Ollama model")
    compile_parser.add_argument("source_json", type=Path, help="JSON output from `ingest`")
    compile_parser.add_argument("--scheme-name", required=True)
    compile_parser.add_argument("--source-kind", choices=["government_resolution", "official_scheme_page", "official_portal", "official_notification"], required=True)
    compile_parser.add_argument("--section", default="Extracted text; section/page must be human-verified")
    compile_parser.add_argument("--output", type=Path, default=Path("data/rule-drafts/compiled-rule-draft.json"))

    args = parser.parse_args()
    if args.command == "ingest":
        record = ingest_public_source(args.url, args.output_dir, respect_robots=not args.ignore_robots)
        print(json.dumps({"title": record.title, "sha256": record.sha256, "final_url": record.final_url, "review_status": record.review_status}, indent=2))
        return

    ingested = json.loads(args.source_json.read_text(encoding="utf-8"))
    text = ingested.get("text", "")
    if len(text) < 50:
        raise SystemExit("Ingested source is missing usable text")
    excerpt = text[:3000]
    source = SourceReference(
        source_name=ingested.get("title") or args.scheme_name,
        source_url=ingested["final_url"],
        source_kind=args.source_kind,
        retrieved_at=datetime.fromisoformat(ingested["retrieved_at"]),
        evidence_excerpt=excerpt,
        evidence_sha256=hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        page_or_section=args.section,
    )
    draft = compile_gr_text_offline(source_text=text, source=source, scheme_name=args.scheme_name)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(draft.model_dump_json(indent=2), encoding="utf-8")
    print(f"Draft saved to {args.output}. It is NOT activated; human review is mandatory.")
