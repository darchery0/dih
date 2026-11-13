
import sqlite3
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
DB = BASE / "library.db"

if not DB.exists():
    raise SystemExit(f"Database not found: {DB}")

# Create a timestamped backup before changing anything.
backup_path = BASE / (
    f"library_before_summaries_{datetime.now():%Y%m%d_%H%M%S}.db"
)

source = sqlite3.connect(DB)
backup = sqlite3.connect(backup_path)

try:
    source.backup(backup)
finally:
    backup.close()

try:
    source.execute("BEGIN IMMEDIATE")

    columns = {
        row[1]
        for row in source.execute("PRAGMA table_info(library)")
    }

    if "summary" not in columns:
        source.execute(
            "ALTER TABLE library ADD COLUMN summary TEXT"
        )
        print("Summary column added.")
    else:
        print("Summary column already exists. No change needed.")

    source.commit()

except Exception:
    source.rollback()
    raise

finally:
    source.close()

print(f"Backup created: {backup_path}")
print("Migration completed successfully.")
