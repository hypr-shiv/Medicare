"""Admin routes — dashboard & management."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request
)
from werkzeug.security import generate_password_hash
from app.routes.db import get_db

admin_bp = Blueprint("admin", __name__)


def admin_required():
    if "user_id" not in session or session.get("user_role") != "admin":
        flash("Access denied.", "danger")
        return False


@admin_bp.route("/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    stats = {
        "doctors":      db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "patients":     db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "appointments": db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        "revenue":      db.execute("SELECT IFNULL(SUM(total),0) FROM billing WHERE payment_status='paid'").fetchone()[0],
    }
    appointments = db.execute(
        """SELECT a.*, p.name AS patient_name, d.name AS doctor_name
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN doctors d  ON a.doctor_id = d.id
           ORDER BY a.date DESC LIMIT 5"""
    ).fetchall()
    return render_template("admin/dashboard.html", stats=stats, appointments=appointments)


@admin_bp.route("/doctors")
def doctors():
    if not admin_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    doctors = db.execute(
        """SELECT d.*, dept.name AS department_name
           FROM doctors d
           LEFT JOIN departments dept ON d.department_id = dept.id
           ORDER BY d.id DESC"""
    ).fetchall()
    return render_template("admin/doctors.html", doctors=doctors)


@admin_bp.route("/doctors/add", methods=["GET", "POST"])
def add_doctor():
    if not admin_required():
        return redirect(url_for("auth.login"))
    db = get_db()

    if request.method == "POST":
        db.execute(
            """INSERT INTO doctors
               (name, email, password, phone, specialization,
                department_id, experience, qualification, fee)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form.get("name"),
                request.form.get("email"),
                generate_password_hash(request.form.get("password")),
                request.form.get("phone"),
                request.form.get("specialization"),
                request.form.get("department_id"),
                request.form.get("experience", 0),
                request.form.get("qualification"),
                request.form.get("fee", 500),
            ),
        )
        db.commit()
        flash("Doctor added.", "success")
        return redirect(url_for("admin.doctors"))

    departments = db.execute("SELECT * FROM departments").fetchall()
    return render_template("admin/add_doctor.html", departments=departments)


@admin_bp.route("/patients")
def patients():
    if not admin_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    patients = db.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    return render_template("admin/patients.html", patients=patients)


@admin_bp.route("/appointments")
def appointments():
    if not admin_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    appointments = db.execute(
        """SELECT a.*, p.name AS patient_name, d.name AS doctor_name
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           JOIN doctors d  ON a.doctor_id = d.id
           ORDER BY a.date DESC"""
    ).fetchall()
    return render_template("admin/appointments.html", appointments=appointments)