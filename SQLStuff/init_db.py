import sqlite3
import os

DB_NAME = "database.db"

def init_db():
    if os.path.exists(DB_NAME):
        print(f"[{DB_NAME}] already exists. Creating backup or reusing existing DB...")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    with open('schema.sql', 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    with open('seed_data.sql', 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("Database successfully initialized and seeded with all records!")

if __name__ == "__main__":
    init_db()