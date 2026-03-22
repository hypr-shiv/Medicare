"""Doctor routes — dashboard, schedule, prescriptions."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request
)
from app.routes.db import get_db

doctor_bp = Blueprint("doctor", __name__)


def doctor_required():
    if "user_id" not in session or session.get("user_role") != "doctor":
        flash("Access denied.", "danger")
        return False


@doctor_bp.route("/dashboard")
def dashboard():
    if not doctor_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    doctor_id = session["user_id"]

    today_appointments = db.execute(
        """SELECT a.*, p.name AS patient_name, p.phone AS patient_phone
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           WHERE a.doctor_id = ? AND a.date = date('now') AND a.status = 'confirmed'
           ORDER BY a.time_slot""",
        (doctor_id,),
    ).fetchall()

    total_patients = db.execute(
        "SELECT COUNT(DISTINCT patient_id) FROM appointments WHERE doctor_id = ?",
        (doctor_id,),
    ).fetchone()[0]

    stats = {
        "today":   len(today_appointments),
        "patients": total_patients,
    }
    return render_template("doctor/dashboard.html", stats=stats, appointments=today_appointments)


@doctor_bp.route("/patients")
def patients():
    if not doctor_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    patients = db.execute(
        """SELECT DISTINCT p.* FROM patients p
           JOIN appointments a ON a.patient_id = p.id
           WHERE a.doctor_id = ?
           ORDER BY p.name""",
        (session["user_id"],),
    ).fetchall()
    return render_template("doctor/patients.html", patients=patients)


@doctor_bp.route("/prescribe", methods=["GET", "POST"])
def prescribe():
    if not doctor_required():
        return redirect(url_for("auth.login"))

    db = get_db()

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        diagnosis  = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        notes      = request.form.get("notes", "")
        doctor_id  = session["user_id"]

        db.execute(
            """INSERT INTO prescriptions
               (patient_id, doctor_id, diagnosis, prescription, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, doctor_id, diagnosis, prescription, notes),
        )
        db.commit()
        flash("Prescription saved.", "success")
        return redirect(url_for("doctor.prescribe"))

    # GET: show patients for this doctor
    patients = db.execute(
        """SELECT DISTINCT p.* FROM patients p
           JOIN appointments a ON a.patient_id = p.id
           WHERE a.doctor_id = ?""",
        (session["user_id"],),
    ).fetchall()
    return render_template("doctor/prescribe.html", patients=patients)


@doctor_bp.route("/appointments")
def appointments():
    if not doctor_required():
        return redirect(url_for("auth.login"))
    db = get_db()
    appointments = db.execute(
        """SELECT a.*, p.name AS patient_name
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           WHERE a.doctor_id = ?
           ORDER BY a.date DESC""",
        (session["user_id"],),
    ).fetchall()
    return render_template("doctor/appointments.html", appointments=appointments)