"""Raw Source Caching and Verbatim Quote Verification Engine.

Manages data/raw/ storage, SHA-256 integrity digests, source manifests,
and programmatic verbatim quote verification against raw source text.
"""

from __future__ import annotations

import hashlib
import json
import logging
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("scheme_navigator.raw_cache")


class RawSourceRecord(BaseModel):
    raw_id: str = Field(..., description="Unique slug for the cached raw source")
    url: str
    tier: str
    sha256: str
    title: str
    language: str
    file_name: str
    retrieved_at: str
    char_count: int


def normalize_text_for_search(text: str) -> str:
    """Normalize text using Unicode NFC and standardized whitespace for robust quote matching."""
    if not text:
        return ""
    # Unicode Normalization Form C (canonical decomposition followed by canonical composition)
    normalized = unicodedata.normalize("NFC", text)
    # Replace non-breaking spaces and zero-width spaces
    normalized = normalized.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    # Normalize varied quotes and dashes
    normalized = normalized.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    normalized = normalized.replace("–", "-").replace("—", "-")
    # Collapse multiple whitespaces and trim
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    return " ".join(" ".join(lines).split())


class RawCacheManager:
    """Manages raw cached government documents and verifies quotes programmatically."""

    def __init__(self, raw_dir: Path | str | None = None) -> None:
        if raw_dir is None:
            base = Path(__file__).resolve().parents[3]
            self.raw_dir = base / "data" / "raw"
        else:
            self.raw_dir = Path(raw_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.raw_dir / "manifest.json"
        self._manifest: Dict[str, Dict[str, Any]] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self.manifest_path.exists():
            try:
                self._manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Could not read raw manifest: {e}")
                self._manifest = {}
        else:
            self._manifest = {}

    def _save_manifest(self) -> None:
        self.manifest_path.write_text(
            json.dumps(self._manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def cache_source_text(
        self,
        raw_id: str,
        text_content: str,
        *,
        url: str,
        title: str,
        tier: str = "tier_1",
        language: str = "mr",
    ) -> RawSourceRecord:
        """Cache raw source text into data/raw/ and record its SHA-256 hash in the manifest."""
        file_name = f"{raw_id}.txt"
        file_path = self.raw_dir / file_name

        # Write text
        file_path.write_text(text_content, encoding="utf-8")

        # Compute SHA-256
        sha256 = hashlib.sha256(text_content.encode("utf-8")).hexdigest()
        retrieved_at = datetime.now(timezone.utc).isoformat()

        record = RawSourceRecord(
            raw_id=raw_id,
            url=url,
            tier=tier,
            sha256=sha256,
            title=title,
            language=language,
            file_name=file_name,
            retrieved_at=retrieved_at,
            char_count=len(text_content),
        )

        self._manifest[raw_id] = record.model_dump()
        self._save_manifest()
        return record

    def get_source_text(self, raw_id: str) -> Optional[str]:
        """Retrieve the exact raw text for a cached source."""
        entry = self._manifest.get(raw_id)
        if not entry:
            return None
        file_path = self.raw_dir / entry["file_name"]
        if not file_path.exists():
            return None
        return file_path.read_text(encoding="utf-8")

    def verify_quote(self, raw_id: str, quote: str) -> bool:
        """Programmatically verify that quote exists verbatim inside the cached source text.
        
        Applies Unicode normalization and standardized whitespace before substring matching.
        """
        source_text = self.get_source_text(raw_id)
        if not source_text or not quote:
            return False

        norm_source = normalize_text_for_search(source_text)
        norm_quote = normalize_text_for_search(quote)

        return norm_quote in norm_source

    def list_sources(self) -> List[Dict[str, Any]]:
        return list(self._manifest.values())
