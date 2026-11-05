"""
Safe, additive migration for the Brooke Point Library checkout system.

Run from the SQLStuff directory:
    python migrate_checkout.py

This script backs up library.db before changing it. It does NOT drop or reseed
any existing tables or records. Each existing book starts with one copy;
adjust total_copies / available_copies later through the admin interface.
"""
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "library.db"


def backup_database(source: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = source.with_name(f"{source.stem}_backup_{stamp}{source.suffix}")

    src = sqlite3.connect(source)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    return backup_path


def table_exists(db: sqlite3.Connection, table_name: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def column_names(db: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in db.execute(f"PRAGMA table_info({table_name})")}


def migrate() -> None:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("I did not create a blank database. Locate or restore your existing library.db first.")
        sys.exit(1)

    backup_path = backup_database(DB_PATH)
    print(f"Backup created: {backup_path.name}")

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")

    try:
        if not table_exists(db, "library") or not table_exists(db, "users"):
            raise RuntimeError(
                "This database does not contain both 'library' and 'users'. "
                "No migration changes were made."
            )

        db.execute("BEGIN IMMEDIATE")

        book_columns = column_names(db, "library")
        if "total_copies" not in book_columns:
            db.execute(
                "ALTER TABLE library ADD COLUMN total_copies "
                "INTEGER NOT NULL DEFAULT 1 CHECK(total_copies >= 0)"
            )
        if "available_copies" not in book_columns:
            db.execute(
                "ALTER TABLE library ADD COLUMN available_copies "
                "INTEGER NOT NULL DEFAULT 1 CHECK(available_copies >= 0)"
            )

        # Existing catalog entries are treated as one physical copy each.
        # If these columns existed already, their current values are preserved.
        db.execute("""
            UPDATE library
               SET total_copies = 1
             WHERE total_copies IS NULL OR total_copies < 0
        """)
        db.execute("""
            UPDATE library
               SET available_copies = total_copies
             WHERE available_copies IS NULL
                OR available_copies < 0
                OR available_copies > total_copies
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                checkout_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT NOT NULL,
                returned_date TEXT,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK(status IN ('active', 'returned')),
                FOREIGN KEY (book_id) REFERENCES library(id) ON DELETE RESTRICT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_type TEXT NOT NULL DEFAULT 'checkout',
                message TEXT NOT NULL,
                loan_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT,
                FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE SET NULL
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_loans_user_status
            ON loans(user_id, status)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_loans_due_status
            ON loans(status, due_date)
        """)
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_reviewed
            ON notifications(reviewed_at, created_at)
        """)

        db.commit()
        print("Checkout migration completed successfully.")
        print("Existing users and books were preserved.")
        print("Each existing book currently has one total and available copy.")
        print("Default checkout period will be 14 days.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
