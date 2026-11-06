#!/usr/bin/env python3
"""Safely apply suggested catalog genres from catalog_genre_mapping.csv."""
import csv, sqlite3, sys
from datetime import datetime
from pathlib import Path
BASE=Path(__file__).resolve().parent
DB=BASE/'library.db'
CSV_PATH=Path(sys.argv[1]).expanduser().resolve() if len(sys.argv)>1 else BASE/'catalog_genre_mapping.csv'
if not DB.is_file(): raise SystemExit(f'Database not found: {DB}')
if not CSV_PATH.is_file(): raise SystemExit(f'Genre mapping not found: {CSV_PATH}')
rows=[]
with CSV_PATH.open(newline='',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        rows.append((r['Genre'].strip(),r['Call Number'].strip(),r['Title'].strip(),r['Author'].strip(),r.get('Confidence','').strip()))
if not rows: raise SystemExit('No genre mappings found; database was not changed.')
backup=DB.with_name('library_before_genre_update_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.db')
con=sqlite3.connect(DB,timeout=15)
bak=sqlite3.connect(backup); con.backup(bak); bak.close()
try:
    cols={x[1] for x in con.execute('PRAGMA table_info(library)')}
    needed={'genre','call_number','title','author','is_active'}
    if not needed.issubset(cols): raise RuntimeError('Library schema is missing required catalog columns: '+', '.join(sorted(needed-cols)))
    con.execute('BEGIN IMMEDIATE')
    updated=0; missing=[]; low=0
    for genre,call,title,author,confidence in rows:
        cur=con.execute('''UPDATE library SET genre=?
            WHERE is_active=1 AND TRIM(COALESCE(call_number,''))=?
              AND TRIM(COALESCE(title,''))=? AND TRIM(COALESCE(author,''))=?''',
            (genre,call,title,author))
        updated += cur.rowcount
        if cur.rowcount==0: missing.append((call,title,author))
        if confidence=='Low': low+=1
    con.commit()
    print('Genre update completed.')
    print(f'Mapping rows: {len(rows)}')
    print(f'Active catalog records updated: {updated}')
    print(f'Unmatched mapping rows: {len(missing)}')
    print(f'Low-confidence suggestions included: {low}')
    print(f'Backup created: {backup}')
    if missing:
        print('First unmatched records:')
        for item in missing[:10]: print(' - ',item)
except Exception:
    con.rollback(); print('Update failed; transaction rolled back. Backup:',backup); raise
finally: con.close()
