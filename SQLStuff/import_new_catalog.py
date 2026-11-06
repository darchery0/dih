#!/usr/bin/env python3
"""
Safely replace the visible Brooke Point Library catalog from
Book Call Numbers_Titles_Author.xlsx.

Run from the SQLStuff folder:
    python3 import_new_catalog.py "/path/to/Book Call Numbers_Titles_Author.xlsx"

This keeps old library rows (and therefore loan foreign keys) but marks them
inactive. Existing users, loans, and notifications are not deleted.
"""
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "library.db"
REQUIRED_HEADERS = [
    "Call Number", "Title", "Author", "Total Copies", "Copies Available"
]

def clean(value):
    return "" if value is None else str(value).strip()

def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            'Usage: python3 import_new_catalog.py "Book Call Numbers_Titles_Author.xlsx"'
        )
    xlsx = Path(sys.argv[1]).expanduser().resolve()
    if not xlsx.is_file():
        raise SystemExit(f"Spreadsheet not found: {xlsx}")
    if not DB_PATH.is_file():
        raise SystemExit(f"Database not found: {DB_PATH}")

    wb = load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb["Library Title & Copy List"] if "Library Title & Copy List" in wb.sheetnames else wb.active
    values = ws.iter_rows(values_only=True)
    headers = [clean(v) for v in next(values)]
    missing = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing:
        raise SystemExit("Missing spreadsheet columns: " + ", ".join(missing))
    indexes = {name: headers.index(name) for name in REQUIRED_HEADERS}

    books = []
    skipped_equipment = 0
    skipped_no_author = 0
    for spreadsheet_row, row in enumerate(values, start=2):
        call_number = clean(row[indexes["Call Number"]])
        title = clean(row[indexes["Title"]])
        author = clean(row[indexes["Author"]])
        if call_number.upper().startswith("EQUIP"):
            skipped_equipment += 1
            continue
        if not author:
            skipped_no_author += 1
            continue
        if not title:
            continue
        try:
            total = int(row[indexes["Total Copies"]] or 1)
            available = int(row[indexes["Copies Available"]] or 0)
        except (TypeError, ValueError):
            raise SystemExit(f"Invalid copy count for: {title}")
        if total < 1 or available < 0 or available > total:
            raise SystemExit(
                f"Invalid inventory for {title!r}: total={total}, available={available}"
            )
        books.append((f"book-list-row-{spreadsheet_row}", call_number, title, author, total, available))

    if not books:
        raise SystemExit("No eligible books found; database was not changed.")

    # Backup via SQLite's online backup API before making any changes.
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.with_name(f"library_before_catalog_replace_{stamp}.db")
    source_db = sqlite3.connect(DB_PATH)
    backup_db = sqlite3.connect(backup)
    source_db.backup(backup_db)
    backup_db.close()

    try:
        source_db.execute("PRAGMA foreign_keys=ON")
        columns = {r[1] for r in source_db.execute("PRAGMA table_info(library)")}
        if not columns:
            raise RuntimeError("The library table does not exist.")
        for name, declaration in (
            ("is_active", "INTEGER NOT NULL DEFAULT 1"),
            ("call_number", "TEXT"),
            ("catalog_import_key", "TEXT"),
        ):
            if name not in columns:
                source_db.execute(f"ALTER TABLE library ADD COLUMN {name} {declaration}")
        columns = {r[1] for r in source_db.execute("PRAGMA table_info(library)")}
        for required in ("id", "title", "author", "genre", "total_copies", "available_copies"):
            if required not in columns:
                raise RuntimeError(
                    f"Your library table is missing required column {required!r}; "
                    "no catalog changes were committed."
                )

        source_db.execute("BEGIN IMMEDIATE")
        # Hide the previous catalog without deleting records referenced by loans.
        source_db.execute("UPDATE library SET is_active=0")

        inserted = 0
        updated = 0
        for import_key, call_number, title, author, total, available in books:
            existing = source_db.execute("""
                SELECT id FROM library WHERE catalog_import_key=?
                ORDER BY id LIMIT 1
            """, (import_key,)).fetchone()

            active_loans = 0
            if existing:
                active_loans = source_db.execute("""
                    SELECT COUNT(*) FROM loans
                    WHERE book_id=? AND status='active'
                """, (existing[0],)).fetchone()[0] if source_db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='loans'"
                ).fetchone() else 0

            safe_available = min(available, max(0, total - active_loans))
            if existing:
                if "lexile" in columns:
                    source_db.execute("""
                        UPDATE library
                        SET title=?, author=?, genre='Uncategorized', lexile=NULL,
                            total_copies=?, available_copies=?, call_number=?, is_active=1
                        WHERE id=?
                    """, (title, author, total, safe_available, call_number, existing[0]))
                else:
                    source_db.execute("""
                        UPDATE library
                        SET title=?, author=?, genre='Uncategorized',
                            total_copies=?, available_copies=?, call_number=?, is_active=1
                        WHERE id=?
                    """, (title, author, total, safe_available, call_number, existing[0]))
                updated += 1
            else:
                if "lexile" in columns:
                    source_db.execute("""
                        INSERT INTO library
                            (title, author, genre, lexile, total_copies, available_copies,
                             call_number, is_active, catalog_import_key)
                        VALUES (?, ?, 'Uncategorized', NULL, ?, ?, ?, 1, ?)
                    """, (title, author, total, available, call_number, import_key))
                else:
                    source_db.execute("""
                        INSERT INTO library
                            (title, author, genre, total_copies, available_copies,
                             call_number, is_active, catalog_import_key)
                        VALUES (?, ?, 'Uncategorized', ?, ?, ?, 1, ?)
                    """, (title, author, total, available, call_number, import_key))
                inserted += 1

        source_db.commit()
        print("Catalog replacement completed successfully.")
        print(f"Eligible spreadsheet entries: {len(books)}")
        print(f"New book records inserted: {inserted}")
        print(f"Matching existing records updated: {updated}")
        print(f"Equipment entries skipped: {skipped_equipment}")
        print(f"Entries with no author skipped: {skipped_no_author}")
        print("Previous catalog records were archived, not deleted.")
        print("Users, loans, and notifications were preserved.")
        print(f"Backup created: {backup}")
    except Exception:
        source_db.rollback()
        print("Import failed. Database changes were rolled back.")
        print(f"Your backup is available at: {backup}")
        raise
    finally:
        source_db.close()
        wb.close()

if __name__ == "__main__":
    main()
