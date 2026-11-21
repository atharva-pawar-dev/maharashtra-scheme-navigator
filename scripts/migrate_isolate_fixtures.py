"""Additive migration and fixture isolation script for MSN databases."""
import shutil
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PROD = REPO_ROOT / "data" / "ingestion.sqlite3"
DB_TEST = REPO_ROOT / "data" / "test_governance.sqlite3"
DB_BACKUP = REPO_ROOT / "data" / "ingestion.sqlite3.backup_before_fixture_isolation"

# 1. Ensure backup exists
if not DB_BACKUP.exists():
    shutil.copy2(DB_PROD, DB_BACKUP)
    print(f"Created backup at {DB_BACKUP}")

# 2. Add is_fixture column to PROD if not exists
conn_prod = sqlite3.connect(DB_PROD)
cur_prod = conn_prod.cursor()
cur_prod.execute("PRAGMA table_info(scheme_completeness_attestations)")
cols = [c[1] for c in cur_prod.fetchall()]
if "is_fixture" not in cols:
    cur_prod.execute("ALTER TABLE scheme_completeness_attestations ADD COLUMN is_fixture INTEGER NOT NULL DEFAULT 0")
    conn_prod.commit()
    print("Added column is_fixture to scheme_completeness_attestations in ingestion.sqlite3")

# 3. Create test database test_governance.sqlite3 from prod backup
shutil.copy2(DB_BACKUP, DB_TEST)
print(f"Created test database at {DB_TEST}")

conn_test = sqlite3.connect(DB_TEST)
cur_test = conn_test.cursor()
cur_test.execute("PRAGMA table_info(scheme_completeness_attestations)")
cols_test = [c[1] for c in cur_test.fetchall()]
if "is_fixture" not in cols_test:
    cur_test.execute("ALTER TABLE scheme_completeness_attestations ADD COLUMN is_fixture INTEGER NOT NULL DEFAULT 0")
cur_test.execute("UPDATE scheme_completeness_attestations SET is_fixture = 1 WHERE scheme_id LIKE 'demo%'")
conn_test.commit()
cur_test.execute("SELECT attestation_id, scheme_id, is_fixture FROM scheme_completeness_attestations WHERE is_fixture = 1")
fixtures_in_test = cur_test.fetchall()
print(f"Test database contains {len(fixtures_in_test)} isolated fixture rows: {fixtures_in_test}")
conn_test.close()

# 4. Remove fixture and test-noise rows from PROD database
# We remove demo-indira-gandhi-old-age-pension, and remove the test runs' duplicate attestations
cur_prod.execute("DELETE FROM scheme_completeness_attestations WHERE scheme_id LIKE 'demo%'")
deleted_fixtures = cur_prod.rowcount
print(f"Deleted {deleted_fixtures} demo fixture row(s) from production database.")

cur_prod.execute("DELETE FROM scheme_completeness_attestations WHERE attested_by IN ('legal_reviewer_invariants', 'advocate_deshmukh_legal_signoff')")
deleted_test_noise = cur_prod.rowcount
print(f"Deleted {deleted_test_noise} transient test-noise row(s) from production database.")

conn_prod.commit()

# Verify production database
cur_prod.execute("SELECT count(*) FROM scheme_completeness_attestations WHERE scheme_id LIKE 'demo%'")
demo_count = cur_prod.fetchone()[0]
cur_prod.execute("SELECT count(*) FROM scheme_completeness_attestations")
total_prod_attestations = cur_prod.fetchone()[0]
cur_prod.execute("SELECT count(DISTINCT scheme_id) FROM scheme_completeness_attestations")
unique_schemes = cur_prod.fetchone()[0]
conn_prod.close()

print(f"\nPROD Database Verification:")
print(f"  Demo fixture attestations in prod: {demo_count} (must be 0)")
print(f"  Total valid scheme attestations in prod: {total_prod_attestations}")
print(f"  Unique legitimate schemes attested in prod: {unique_schemes}")
assert demo_count == 0, "Demo fixture still present in production database!"
assert unique_schemes == 16, f"Expected 16 genuine schemes, got {unique_schemes}"
print("\nMigration and fixture isolation successfully verified!")
