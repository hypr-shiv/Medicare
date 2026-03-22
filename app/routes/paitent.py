"""Patient routes — dashboard & profile."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request
)
from app.routes.db import get_db

patient_bp = Blueprint("patient", __name__)


def patient_required():
    if "user_id" not in session or session.get("user_role") != "patient":
        flash("Access denied.", "danger")
        return False


@patient_bp.route("/dashboard")
def dashboard():
    if not patient_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    patient_id = session["user_id"]

    appointments = db.execute(
        """SELECT a.*, d.name AS doctor_name, dept.name AS dept_name
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           LEFT JOIN departments dept ON d.department_id = dept.id
           WHERE a.patient_id = ?
           ORDER BY a.date DESC""",
        (patient_id,),
    ).fetchall()

    prescriptions = db.execute(
        """SELECT pr.*, d.name AS doctor_name
           FROM prescriptions pr
           JOIN doctors d ON pr.doctor_id = d.id
           WHERE pr.patient_id = ?
           ORDER BY pr.created_at DESC LIMIT 5""",
        (patient_id,),
    ).fetchall()

    return render_template(
        "patient/dashboard.html",
        appointments=appointments,
        prescriptions=prescriptions,
    )


@patient_bp.route("/profile")
def profile():
    if not patient_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    patient = db.execute(
        "SELECT * FROM patients WHERE id = ?", (session["user_id"],)
    ).fetchone()
    return render_template("patient/profile.html", patient=patient)