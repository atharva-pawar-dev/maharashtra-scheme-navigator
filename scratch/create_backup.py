import shutil
import datetime
from pathlib import Path

def backup():
    root = Path(r"c:\Users\Admin\Downloads\scheme-navigator\scheme-navigator")
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = Path(r"c:\Users\Admin\Downloads\scheme-navigator") / f"backup-scheme-integration-{ts}"
    print(f"Backing up {root} to {backup_dir}...")

    def ignore_patterns(dir, files):
        return {f for f in files if f in {".venv", "backups", "test_backups", "__pycache__", ".pytest_cache", "security_audit.log", "interviews.sqlite3-wal", "interviews.sqlite3-shm"}}

    shutil.copytree(root, backup_dir, ignore=ignore_patterns)
    print(f"Backup created successfully at: {backup_dir}")

if __name__ == "__main__":
    backup()
