from pathlib import Path
import json

raw_dir = Path("data/raw")
for p in sorted(raw_dir.glob("*.txt")):
    print("="*60)
    print(f"FILE: {p.name}")
    content = p.read_text(encoding="utf-8")
    print(content.strip())
