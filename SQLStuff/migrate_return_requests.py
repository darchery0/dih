"""Safe, additive migration for borrower-initiated return requests."""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "library.db"
if not DB.exists():
    raise SystemExit(f"Database not found: {DB}. Run this from the folder containing library.db.")

con = sqlite3.connect(DB)
try:
    con.execute("PRAGMA busy_timeout=10000")
    columns = {row[1] for row in con.execute("PRAGMA table_info(loans)")}
    if not columns:
        raise SystemExit("The loans table was not found. Run the checkout migration first.")
    if "return_requested_at" not in columns:
        con.execute("ALTER TABLE loans ADD COLUMN return_requested_at TEXT")
    con.commit()
    print("Return-request migration completed. Existing loans and books were preserved.")
finally:
    con.close()
