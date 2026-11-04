
import os
import sqlite3
import sys
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, session, render_template, redirect
from werkzeug.security import generate_password_hash, check_password_hash

BASE = Path(__file__).resolve().parent
DB = BASE / "library.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize():
    db = connect()
    try:
        for filename in ("schema.sql", "seed_data.sql"):
            path = BASE / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing {filename}")
            db.executescript(path.read_text(encoding="utf-8"))

        # Replace the supplied placeholder password hashes
        # with real Werkzeug password hashes for demo accounts.
        demo_passwords = {
            "admin_sarah": "Admin123!",
            "volunteer_tim": "Volunteer123!",
            "citizen_jane": "Citizen123!",
            "mmichael": "Citizen123!",
            "cdarya": "Citizen123!",
            "csamman": "Citizen123!",
        }

        for username, password in demo_passwords.items():
            db.execute(
                "UPDATE users SET password_hash=? WHERE username=?",
                (generate_password_hash(password), username)
            )

        db.commit()
        print("Database initialized successfully.")
    finally:
        db.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(error="Please log in."), 401
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                return jsonify(error="Permission denied."), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def rows(query, params=()):
    db = connect()
    try:
        return [dict(r) for r in db.execute(query, params).fetchall()]
    finally:
        db.close()


def error(message, status=400):
    return jsonify(error=message), status


@app.get("/")
def home():
    db = connect()
    try:
        all_books = [
            dict(book) for book in db.execute(
                "SELECT * FROM library ORDER BY title"
            ).fetchall()
        ]
        requests = [
            dict(req) for req in db.execute("""
                SELECT r.*, u.username
                FROM requests r
                JOIN users u ON r.user_id = u.user_id
                ORDER BY r.request_date DESC
            """).fetchall()
        ]
        resources = [
            dict(res) for res in db.execute("""
                SELECT cr.*, u.username AS manager
                FROM community_resources cr
                LEFT JOIN users u
                ON cr.managed_by_user_id = u.user_id
                ORDER BY cr.resource_name
            """).fetchall()
        ]
    finally:
        db.close()

    return render_template(
        "index.html",
        all_books=all_books,
        featured_books=all_books[:10],
        requests=requests,
        resources=resources
    )
@app.get("/books")
def books_page():
    db = connect()
    try:
        all_books = [
            dict(book) for book in db.execute(
                "SELECT * FROM library ORDER BY title"
            ).fetchall()
        ]
    finally:
        db.close()

    return render_template("books.html", all_books=all_books)

@app.get("/login")
def login_page():
    if "user_id" in session:
        return redirect("/")
    return render_template("login.html")


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    db = connect()
    try:
        user = db.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
    finally:
        db.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return error("Invalid username or password.", 401)

    session.clear()
    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["role"] = user["user_role"]

    return jsonify(
        username=user["username"],
        role=user["user_role"]
    )


@app.post("/api/logout")
@login_required
def logout():
    session.clear()
    return jsonify(success=True)


@app.get("/api/me")
@login_required
def me():
    return jsonify(
        username=session["username"],
        role=session["role"]
    )


@app.get("/api/dashboard")
@login_required
def dashboard():
    db = connect()
    try:
        result = {
            "books": db.execute(
                "SELECT COUNT(*) FROM library"
            ).fetchone()[0],
            "users": db.execute(
                "SELECT COUNT(*) FROM users"
            ).fetchone()[0],
            "requests": db.execute(
                "SELECT COUNT(*) FROM requests"
            ).fetchone()[0],
            "pending": db.execute(
                "SELECT COUNT(*) FROM requests WHERE status='pending'"
            ).fetchone()[0],
            "donations": db.execute(
                "SELECT COUNT(*) FROM donations"
            ).fetchone()[0],
            "resources": db.execute(
                "SELECT COUNT(*) FROM community_resources"
            ).fetchone()[0],
        }
        return jsonify(result)
    finally:
        db.close()


@app.get("/api/books")
@login_required
def get_books():
    genre = request.args.get("genre", "").strip()
    search = request.args.get("search", "").strip()

    sql = "SELECT * FROM library WHERE 1=1"
    params = []

    if genre:
        sql += " AND LOWER(genre)=LOWER(?)"
        params.append(genre)

    if search:
        sql += " AND (title LIKE ? OR author LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += " ORDER BY title"
    return jsonify(rows(sql, params))


@app.post("/api/books")
@roles_required("admin", "volunteer")
def add_book():
    data = request.get_json(silent=True) or {}

    title = data.get("title", "").strip()
    author = data.get("author", "").strip()
    genre = data.get("genre", "").strip()
    lexile = data.get("lexile")

    if not title or not author or not genre:
        return error("Title, author, and genre are required.")

    if genre.lower() not in {
        "fantasy", "mystery", "romance"
    }:
        return error("Use Fantasy, Mystery, or Romance.")

    try:
        lexile = int(lexile) if lexile not in (None, "") else None
        if lexile is not None and lexile < 0:
            return error("Lexile cannot be negative.")
    except (TypeError, ValueError):
        return error("Lexile must be a number.")

    db = connect()
    try:
        cursor = db.execute(
            "INSERT INTO library(title, author, lexile, genre) VALUES(?,?,?,?)",
            (title, author, lexile, genre)
        )
        db.commit()
        return jsonify(id=cursor.lastrowid), 201
    except sqlite3.Error:
        return error("Could not add book.")
    finally:
        db.close()


@app.put("/api/books/<int:book_id>")
@roles_required("admin", "volunteer")
def edit_book(book_id):
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    author = data.get("author", "").strip()
    genre = data.get("genre", "").strip()
    lexile = data.get("lexile")

    if not title or not author or not genre:
        return error("Title, author, and genre are required.")

    if genre.lower() not in {"fantasy", "mystery", "romance"}:
        return error("Invalid genre.")

    try:
        lexile = int(lexile) if lexile not in (None, "") else None
        if lexile is not None and lexile < 0:
            return error("Invalid Lexile.")
    except (TypeError, ValueError):
        return error("Lexile must be a number.")

    db = connect()
    try:
        cursor = db.execute(
            """UPDATE library SET title=?, author=?, lexile=?, genre=?
               WHERE id=?""",
            (title, author, lexile, genre, book_id)
        )
        db.commit()
        if not cursor.rowcount:
            return error("Book not found.", 404)
        return jsonify(success=True)
    finally:
        db.close()


@app.delete("/api/books/<int:book_id>")
@roles_required("admin")
def delete_book(book_id):
    db = connect()
    try:
        cursor = db.execute("DELETE FROM library WHERE id=?", (book_id,))
        db.commit()
        if not cursor.rowcount:
            return error("Book not found.", 404)
        return jsonify(success=True)
    finally:
        db.close()


@app.get("/api/requests")
@login_required
def get_requests():
    role = session["role"]
    user_id = session["user_id"]

    sql = """
        SELECT r.*, u.username
        FROM requests r JOIN users u ON r.user_id=u.user_id
    """
    params = []

    if role == "citizen":
        sql += " WHERE r.user_id=?"
        params.append(user_id)

    sql += " ORDER BY r.request_date DESC"
    return jsonify(rows(sql, params))


@app.post("/api/requests")
@login_required
def add_request():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    author = data.get("author", "").strip()
    genre = data.get("genre", "").strip()

    try:
        quantity = int(data.get("quantity", 1))
        if quantity < 1 or quantity > 100:
            return error("Quantity must be between 1 and 100.")
    except (TypeError, ValueError):
        return error("Invalid quantity.")

    if not title or not author or not genre:
        return error("Title, author, and genre are required.")

    db = connect()
    try:
        cursor = db.execute(
            """INSERT INTO requests
            (user_id, request_title, request_author, request_genre,
             quantity_requested)
            VALUES(?,?,?,?,?)""",
            (session["user_id"], title, author, genre, quantity)
        )
        db.commit()
        return jsonify(id=cursor.lastrowid), 201
    finally:
        db.close()


@app.patch("/api/requests/<int:request_id>")
@roles_required("admin", "volunteer")
def update_request(request_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")

    if status not in ("pending", "approved", "rejected"):
        return error("Invalid request status.")

    db = connect()
    try:
        cursor = db.execute(
            "UPDATE requests SET status=? WHERE request_id=?",
            (status, request_id)
        )
        db.commit()
        if not cursor.rowcount:
            return error("Request not found.", 404)
        return jsonify(success=True)
    finally:
        db.close()


@app.get("/api/resources")
@login_required
def get_resources():
    return jsonify(rows("""
        SELECT cr.*, u.username AS manager
        FROM community_resources cr
        LEFT JOIN users u ON cr.managed_by_user_id=u.user_id
        ORDER BY cr.resource_name
    """))


@app.get("/api/donations")
@login_required
def get_donations():
    return jsonify(rows("""
        SELECT d.*, u.username, cr.resource_name
        FROM donations d
        JOIN users u ON d.user_id=u.user_id
        JOIN community_resources cr ON d.resource_id=cr.resource_id
        ORDER BY d.donation_date DESC
    """))


@app.post("/api/donations")
@login_required
def add_donation():
    data = request.get_json(silent=True) or {}

    try:
        resource_id = int(data.get("resource_id"))
        quantity = int(data.get("quantity", 1))
        if quantity < 1 or quantity > 10000:
            return error("Invalid donation quantity.")
    except (TypeError, ValueError):
        return error("Select a resource and valid quantity.")

    db = connect()
    try:
        resource = db.execute(
            "SELECT resource_id FROM community_resources WHERE resource_id=?",
            (resource_id,)
        ).fetchone()

        if not resource:
            return error("Resource not found.", 404)

        cursor = db.execute(
            """INSERT INTO donations
            (user_id, resource_id, quantity_donated, notes)
            VALUES(?,?,?,?)""",
            (
                session["user_id"],
                resource_id,
                quantity,
                data.get("notes", "").strip()
            )
        )

        db.execute(
            """UPDATE community_resources
               SET quantity_available=quantity_available+?
               WHERE resource_id=?""",
            (quantity, resource_id)
        )

        db.commit()
        return jsonify(id=cursor.lastrowid), 201
    finally:
        db.close()


@app.get("/api/users")
@roles_required("admin")
def get_users():
    return jsonify(rows("""
        SELECT user_id, username, email, user_role, account_created
        FROM users ORDER BY username
    """))


@app.post("/api/users")
@roles_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "citizen")

    if not username or not email or len(password) < 8:
        return error("Username, email, and password (8+ characters) required.")

    if role not in ("admin", "volunteer", "citizen"):
        return error("Invalid role.")

    db = connect()
    try:
        cursor = db.execute(
            """INSERT INTO users(username, password_hash, email, user_role)
               VALUES(?,?,?,?)""",
            (username, generate_password_hash(password), email, role)
        )
        db.commit()
        return jsonify(id=cursor.lastrowid), 201
    except sqlite3.IntegrityError:
        return error("Username or email already exists.")
    finally:
        db.close()


if __name__ == "__main__":
    if "--init" in sys.argv:
        initialize()
    else:
        if not DB.exists():
            print("Run: python app.py --init")
            sys.exit(1)
        app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
