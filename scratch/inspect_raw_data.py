import json
import sqlite3
from pathlib import Path

# Demo schemes
demo_p = Path('data/demo/schemes.json')
demo_schemes = json.loads(demo_p.read_text(encoding='utf-8')) if demo_p.exists() else []
print(f'Demo schemes in data/demo/schemes.json: {len(demo_schemes)}')
for ds in demo_schemes:
    print(f"  id={ds.get('scheme_id')} name={ds.get('scheme_name')} is_demo={ds.get('is_demo')} pub_auth={ds.get('publication_authorized')}")

# Candidates
cand_p = Path('data/candidates/candidate_schemes.json')
cand_schemes = json.loads(cand_p.read_text(encoding='utf-8')) if cand_p.exists() else []
print(f'Candidate schemes in data/candidates/candidate_schemes.json: {len(cand_schemes)}')
for cs in cand_schemes:
    print(f"  id={cs.get('scheme_id')} name={cs.get('scheme_name')} status={cs.get('rule_status')} pub_auth={cs.get('publication_authorized')}")

# Ingestion SQLite
db_p = Path('data/ingestion.sqlite3')
if db_p.exists():
    conn = sqlite3.connect(db_p)
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f'Ingestion SQLite tables: {tables}')
    for t in tables:
        cnt = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f'  Table {t}: {cnt} rows')
        # Print sample
        rows = cur.execute(f"SELECT * FROM {t} LIMIT 3").fetchall()
        for r in rows:
            print(f'    sample: {r[:3]}')
