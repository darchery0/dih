BROOKE POINT LIBRARY — GENRE CLASSIFICATION

Files:
- Brooke_Point_Catalog_With_Genres.xlsx: original inventory with Suggested Genre,
  Classification Confidence, and Classification Basis columns, plus Genre Summary.
- catalog_genre_mapping.csv: genre values for the database update script.
- update_book_genres.py: makes a SQLite backup and updates only matching active
  catalog rows. It does not delete books, users, loans, or notifications.

To apply in Codespaces:
1. Copy all three files into SQLStuff beside app.py and library.db.
2. Stop Flask (Ctrl+C).
3. Run:
   python3 update_book_genres.py
4. Start the site again:
   python3 app.py

The script uses Call Number + Title + Author to match each active book and makes
its own timestamped database backup before changing anything.

IMPORTANT CLASSIFICATION NOTE:
This is a first-pass suggested classification, not a verified bibliographic record
for every title. Nonfiction genres are mapped from Dewey-style call-number ranges.
Picture books and graphic novels use their collection call numbers. FIC titles are
assigned from recognizable title clues; titles without a clear clue are labeled
General Fiction with Low confidence. Check the Classification Confidence column
before relying on the suggestions as definitive. Web checks were performed on a
small sample of titles, not every title in the 1,194-book catalog.
