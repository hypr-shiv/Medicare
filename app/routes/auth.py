"""Authentication routes — login, register, logout."""
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes.db import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role     = request.form.get("role", "patient")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("auth/login.html", role=role)

        table_map = {"admin": "admins", "doctor": "doctors", "patient": "patients"}
        table = table_map.get(role)
        if not table:
            flash("Invalid role.", "danger")
            return render_template("auth/login.html", role=role)

        db = get_db()
        user = db.execute(
            f"SELECT * FROM {table} WHERE email = ?", (email,)
        ).fetchone()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"]   = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = role
            flash(f"Welcome, {user['name']}!", "success")

            redirects = {
                "admin":   "admin.dashboard",
                "doctor":  "doctor.dashboard",
                "patient": "patient.dashboard",
            }
            return redirect(url_for(redirects.get(role, "main.index")))
        else:
            flash("Invalid email or password.", "danger")

    role = request.args.get("role", "patient")
    return render_template("auth/login.html", role=role)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name        = request.form.get("name", "").strip()
        email       = request.form.get("email", "").strip().lower()
        password    = request.form.get("password", "")
        confirm     = request.form.get("confirm_password", "")
        phone       = request.form.get("phone", "").strip()
        dob         = request.form.get("dob", "").strip()
        gender      = request.form.get("gender", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        address     = request.form.get("address", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not email:
            errors.append("Email is required.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html")

        db = get_db()
        existing = db.execute(
            "SELECT id FROM patients WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")

        db.execute(
            """INSERT INTO patients
               (name, email, password, phone, dob, gender, blood_group, address)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, email, generate_password_hash(password),
             phone, dob, gender, blood_group, address),
        )
        db.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))