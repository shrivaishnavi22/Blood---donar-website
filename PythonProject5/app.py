from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = "blood_donor_secret_key_2024"

DB = "donors.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            blood TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- DONOR REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name  = request.form["name"].strip()
        phone = request.form["phone"].strip()
        city  = request.form["city"].strip()
        blood = request.form["blood"].strip()

        if not all([name, phone, city, blood]):
            flash("All fields are required.", "error")
            return render_template("register.html")

        conn = get_db()
        conn.execute(
            "INSERT INTO donors (name, phone, city, blood) VALUES (?, ?, ?, ?)",
            (name, phone, city, blood)
        )
        conn.commit()
        conn.close()
        flash("Registered successfully! Thank you for being a donor.", "success")
        return redirect(url_for("register"))

    return render_template("register.html")

# ---------- SEARCH ----------
@app.route("/search", methods=["GET", "POST"])
def search():
    donors = []
    searched = False
    if request.method == "POST":
        city  = request.form.get("city", "").strip()
        blood = request.form.get("blood", "").strip()
        searched = True

        conn = get_db()
        query = "SELECT * FROM donors WHERE 1=1"
        params = []
        if city:
            query += " AND LOWER(city) LIKE ?"
            params.append(f"%{city.lower()}%")
        if blood:
            query += " AND blood = ?"
            params.append(blood)
        donors = conn.execute(query, params).fetchall()
        conn.close()

    return render_template("search.html", donors=donors, searched=searched)

# ---------- ADMIN SIGNUP ----------
@app.route("/admin_signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        email    = request.form["email"].strip()
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not all([email, username, password]):
            flash("All fields are required.", "error")
            return render_template("admin_signup.html")

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM admin WHERE username=? OR email=?", (username, email)
        ).fetchone()

        if existing:
            flash("Username or email already exists.", "error")
            conn.close()
            return render_template("admin_signup.html")

        conn.execute(
            "INSERT INTO admin (email, username, password) VALUES (?, ?, ?)",
            (email, username, hash_password(password))
        )
        conn.commit()
        conn.close()
        flash("Account created! Please login.", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin_signup.html")

# ---------- ADMIN LOGIN ----------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, hash_password(password))
        ).fetchone()
        conn.close()

        if admin:
            session["admin_id"]       = admin["id"]
            session["admin_username"] = admin["username"]
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("admin_login.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("admin_login"))

    conn = get_db()
    donors = conn.execute("SELECT * FROM donors ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", donors=donors)

# ---------- ADMIN LOGOUT ----------
@app.route("/admin_logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)