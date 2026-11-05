import os
import sqlite3
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

BASE = Path(__file__).resolve().parent
DB = BASE / "library.db"
LOAN_DAYS = 14

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-before-deployment")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def connect():
    db = sqlite3.connect(DB, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify(error="Please log in."), 401
            return redirect(url_for("login_page"))
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                if request.path.startswith("/api/"):
                    return jsonify(error="Permission denied."), 403
                return redirect(url_for("home"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def error(message, status=400):
    return jsonify(error=message), status


def rows(query, params=()):
    db = connect()
    try:
        return [dict(row) for row in db.execute(query, params).fetchall()]
    finally:
        db.close()


@app.get("/")
def home():
    books = rows("""
        SELECT id, title, author, genre, lexile, total_copies, available_copies
        FROM library ORDER BY title LIMIT 8
    """)
    return render_template("index.html", books=books)


@app.get("/books")
def books_page():
    books = rows("""
        SELECT id, title, author, genre, lexile, total_copies, available_copies
        FROM library ORDER BY title
    """)
    return render_template("book.html", books=books)


@app.get("/login")
def login_page():
    if session.get("user_id"):
        return redirect(url_for("admin_page" if session.get("role") == "admin" else "my_account"))
    return render_template("login.html")


@app.get("/my-account")
@login_required
def my_account():
    return render_template("my_account.html")


@app.get("/admin")
@roles_required("admin")
def admin_page():
    return render_template("admin.html")


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = data.get("password", "")
    db = connect()
    try:
        user = db.execute(
            "SELECT user_id, username, password_hash, user_role FROM users WHERE username=?",
            (username,)
        ).fetchone()
    finally:
        db.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return error("Invalid username or password.", 401)

    session.clear()
    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["role"] = user["user_role"]
    destination = "/admin" if user["user_role"] == "admin" else "/my-account"
    return jsonify(success=True, username=user["username"], role=user["user_role"], redirect=destination)


@app.post("/api/logout")
@login_required
def logout():
    session.clear()
    return jsonify(success=True)


@app.get("/api/me")
@login_required
def me():
    return jsonify(username=session["username"], role=session["role"])


@app.get("/api/books")
def get_books():
    search = request.args.get("search", "").strip()
    genre = request.args.get("genre", "").strip()
    sql = """
        SELECT id, title, author, genre, lexile, total_copies, available_copies
        FROM library WHERE 1=1
    """
    params = []
    if search:
        sql += " AND (title LIKE ? OR author LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if genre:
        sql += " AND LOWER(genre)=LOWER(?)"
        params.append(genre)
    sql += " ORDER BY title"
    return jsonify(rows(sql, params))


@app.post("/api/books/<int:book_id>/checkout")
@login_required
def checkout_book(book_id):
    db = connect()
    try:
        # Serialize competing checkout attempts so inventory cannot go negative.
        db.execute("BEGIN IMMEDIATE")
        book = db.execute(
            "SELECT title, available_copies FROM library WHERE id=?", (book_id,)
        ).fetchone()
        if not book:
            db.rollback()
            return error("Book not found.", 404)
        if book["available_copies"] < 1:
            db.rollback()
            return error("This book is currently unavailable.", 409)

        active = db.execute("""
            SELECT 1 FROM loans
            WHERE book_id=? AND user_id=? AND status='active'
        """, (book_id, session["user_id"])).fetchone()
        if active:
            db.rollback()
            return error("You already have this book checked out.", 409)

        due_date = (date.today() + timedelta(days=LOAN_DAYS)).isoformat()
        db.execute("""
            UPDATE library SET available_copies=available_copies-1
            WHERE id=? AND available_copies>0
        """, (book_id,))
        if db.execute("SELECT changes()").fetchone()[0] != 1:
            db.rollback()
            return error("This book is no longer available.", 409)

        cursor = db.execute("""
            INSERT INTO loans(book_id, user_id, due_date)
            VALUES(?,?,?)
        """, (book_id, session["user_id"], due_date))
        db.execute("""
            INSERT INTO notifications(notification_type, message, loan_id)
            VALUES('checkout', ?, ?)
        """, (f"{session['username']} checked out “{book['title']}”.", cursor.lastrowid))
        db.commit()
        return jsonify(success=True, due_date=due_date), 201
    except sqlite3.Error:
        db.rollback()
        app.logger.exception("Checkout failed")
        return error("The checkout could not be completed.", 500)
    finally:
        db.close()


@app.get("/api/my-loans")
@login_required
def my_loans():
    return jsonify(rows("""
        SELECT l.loan_id, l.checkout_date, l.due_date, l.returned_date, l.status,
               b.title, b.author,
               CASE WHEN l.status='active' AND date(l.due_date)<date('now')
                    THEN 1 ELSE 0 END AS overdue
        FROM loans l JOIN library b ON b.id=l.book_id
        WHERE l.user_id=?
        ORDER BY CASE WHEN l.status='active' THEN 0 ELSE 1 END,
                 l.checkout_date DESC
    """, (session["user_id"],)))


@app.get("/api/admin/summary")
@roles_required("admin")
def admin_summary():
    result = {
        "titles": rows("SELECT COUNT(*) AS n FROM library")[0]["n"],
        "copies": rows("SELECT COALESCE(SUM(total_copies),0) AS n FROM library")[0]["n"],
        "available": rows("SELECT COALESCE(SUM(available_copies),0) AS n FROM library")[0]["n"],
        "active": rows("SELECT COUNT(*) AS n FROM loans WHERE status='active'")[0]["n"],
        "overdue": rows("SELECT COUNT(*) AS n FROM loans WHERE status='active' AND date(due_date)<date('now')")[0]["n"],
        "unreviewed": rows("SELECT COUNT(*) AS n FROM notifications WHERE reviewed_at IS NULL")[0]["n"],
        "users": rows("SELECT COUNT(*) AS n FROM users")[0]["n"],
    }
    return jsonify(result)


@app.get("/api/admin/loans")
@roles_required("admin")
def admin_loans():
    return jsonify(rows("""
        SELECT l.loan_id, l.checkout_date, l.due_date, l.returned_date, l.status,
               b.title, b.author, u.username,
               CASE WHEN l.status='active' AND date(l.due_date)<date('now')
                    THEN 1 ELSE 0 END AS overdue
        FROM loans l
        JOIN library b ON b.id=l.book_id
        JOIN users u ON u.user_id=l.user_id
        ORDER BY CASE WHEN l.status='active' THEN 0 ELSE 1 END,
                 l.due_date ASC
    """))


@app.post("/api/admin/loans/<int:loan_id>/return")
@roles_required("admin")
def return_book(loan_id):
    db = connect()
    try:
        db.execute("BEGIN IMMEDIATE")
        loan = db.execute("""
            SELECT book_id, status FROM loans WHERE loan_id=?
        """, (loan_id,)).fetchone()
        if not loan:
            db.rollback()
            return error("Loan not found.", 404)
        if loan["status"] != "active":
            db.rollback()
            return error("This book has already been returned.", 409)

        db.execute("""
            UPDATE loans SET status='returned', returned_date=CURRENT_TIMESTAMP
            WHERE loan_id=? AND status='active'
        """, (loan_id,))
        db.execute("""
            UPDATE library SET available_copies=available_copies+1,
                total_copies=CASE WHEN total_copies<available_copies+1
                                  THEN available_copies+1 ELSE total_copies END
            WHERE id=?
        """, (loan["book_id"],))
        db.commit()
        return jsonify(success=True)
    except sqlite3.Error:
        db.rollback()
        app.logger.exception("Return failed")
        return error("The return could not be recorded.", 500)
    finally:
        db.close()


@app.get("/api/admin/notifications")
@roles_required("admin")
def admin_notifications():
    return jsonify(rows("""
        SELECT notification_id, notification_type, message, created_at, reviewed_at
        FROM notifications ORDER BY reviewed_at IS NOT NULL, created_at DESC
    """))


@app.post("/api/admin/notifications/<int:notification_id>/review")
@roles_required("admin")
def review_notification(notification_id):
    db = connect()
    try:
        cursor = db.execute("""
            UPDATE notifications SET reviewed_at=CURRENT_TIMESTAMP
            WHERE notification_id=? AND reviewed_at IS NULL
        """, (notification_id,))
        db.commit()
        if cursor.rowcount == 0:
            return error("Notification not found or already reviewed.", 404)
        return jsonify(success=True)
    finally:
        db.close()


@app.post("/api/admin/books")
@roles_required("admin")
def admin_add_book():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    genre = str(data.get("genre", "")).strip()
    try:
        copies = int(data.get("total_copies", 1))
        lexile = int(data["lexile"]) if data.get("lexile") not in (None, "") else None
    except (TypeError, ValueError):
        return error("Copies and Lexile must be whole numbers.")
    if not title or not author or not genre or copies < 1:
        return error("Title, author, genre, and at least one copy are required.")
    if lexile is not None and lexile < 0:
        return error("Lexile cannot be negative.")
    db = connect()
    try:
        cursor = db.execute("""
            INSERT INTO library(title, author, genre, lexile, total_copies, available_copies)
            VALUES(?,?,?,?,?,?)
        """, (title, author, genre, lexile, copies, copies))
        db.commit()
        return jsonify(id=cursor.lastrowid), 201
    except sqlite3.Error:
        db.rollback()
        return error("Could not add this book.")
    finally:
        db.close()


@app.put("/api/admin/books/<int:book_id>")
@roles_required("admin")
def admin_edit_book(book_id):
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    author = str(data.get("author", "")).strip()
    genre = str(data.get("genre", "")).strip()
    try:
        total = int(data.get("total_copies"))
    except (TypeError, ValueError):
        return error("Total copies must be a whole number.")
    if not title or not author or not genre or total < 1:
        return error("Enter a title, author, genre, and at least one copy.")
    db = connect()
    try:
        book = db.execute(
            "SELECT available_copies FROM library WHERE id=?", (book_id,)
        ).fetchone()
        if not book:
            return error("Book not found.", 404)
        checked_out = db.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id=? AND status='active'",
            (book_id,)
        ).fetchone()[0]
        if total < checked_out:
            return error(f"At least {checked_out} copies are currently checked out.")
        available = total - checked_out
        db.execute("""
            UPDATE library SET title=?, author=?, genre=?, total_copies=?,
                available_copies=? WHERE id=?
        """, (title, author, genre, total, available, book_id))
        db.commit()
        return jsonify(success=True)
    finally:
        db.close()


@app.delete("/api/admin/books/<int:book_id>")
@roles_required("admin")
def admin_delete_book(book_id):
    db = connect()
    try:
        active = db.execute(
            "SELECT COUNT(*) FROM loans WHERE book_id=? AND status='active'",
            (book_id,)
        ).fetchone()[0]
        if active:
            return error("Cannot delete a book while copies are checked out.", 409)
        cursor = db.execute("DELETE FROM library WHERE id=?", (book_id,))
        db.commit()
        if not cursor.rowcount:
            return error("Book not found.", 404)
        return jsonify(success=True)
    except sqlite3.IntegrityError:
        db.rollback()
        return error("This book has borrowing history and cannot be deleted.", 409)
    finally:
        db.close()


@app.get("/api/admin/users")
@roles_required("admin")
def admin_users():
    return jsonify(rows("""
        SELECT user_id, username, email, user_role, account_created
        FROM users ORDER BY username
    """))


@app.post("/api/admin/users")
@roles_required("admin")
def admin_create_user():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = data.get("password", "")
    role = data.get("role", "citizen")
    if not username or not email or len(password) < 8:
        return error("Username, email, and a password of at least 8 characters are required.")
    if role not in ("admin", "volunteer", "citizen"):
        return error("Invalid role.")
    db = connect()
    try:
        cursor = db.execute("""
            INSERT INTO users(username, password_hash, email, user_role)
            VALUES(?,?,?,?)
        """, (username, generate_password_hash(password), email, role))
        db.commit()
        return jsonify(id=cursor.lastrowid), 201
    except sqlite3.IntegrityError:
        return error("Username or email already exists.")
    finally:
        db.close()


@app.patch("/api/admin/users/<int:user_id>/role")
@roles_required("admin")
def admin_change_role(user_id):
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if role not in ("admin", "volunteer", "citizen"):
        return error("Invalid role.")
    if user_id == session["user_id"] and role != "admin":
        return error("You cannot remove your own admin role.")
    db = connect()
    try:
        cursor = db.execute("UPDATE users SET user_role=? WHERE user_id=?", (role, user_id))
        db.commit()
        if not cursor.rowcount:
            return error("User not found.", 404)
        return jsonify(success=True)
    finally:
        db.close()


if __name__ == "__main__":
    if not DB.exists():
        raise SystemExit(
            f"Database not found at {DB}. Restore library.db and run migrate_checkout.py first."
        )
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
