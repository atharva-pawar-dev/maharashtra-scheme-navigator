from pathlib import Path

raw_dir = Path("data/raw")
files = [
    "gr_sgnay_2023.txt",
    "gr_shravanbal_2023.txt",
    "gr_vayoshri_2024.txt",
    "gr_ramai_gharkul.txt",
    "gr_namo_shetkari_2023.txt",
    "gr_mmlby_2024.txt",
]
for f in files:
    p = raw_dir / f
    if p.exists():
        print("="*60)
        print(f"FILE: {f}")
        print(p.read_text(encoding="utf-8").strip())
