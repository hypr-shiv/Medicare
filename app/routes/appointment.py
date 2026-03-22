"""Appointment routes — book & cancel."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request
)
from app.routes.db import get_db

appointment_bp = Blueprint("appointment", __name__)


def login_required():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return False


@appointment_bp.route("/book", methods=["GET", "POST"])
def book():
    if not login_required():
        return redirect(url_for("auth.login"))

    db = get_db()

    if request.method == "POST":
        doctor_id  = request.form.get("doctor_id")
        date       = request.form.get("date")
        time_slot  = request.form.get("time_slot")
        reason     = request.form.get("reason", "")
        patient_id = session["user_id"]

        if not doctor_id or not date or not time_slot:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for("appointment.book"))

        db.execute(
            """INSERT INTO appointments
               (patient_id, doctor_id, date, time_slot, reason, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (patient_id, doctor_id, date, time_slot, reason),
        )
        db.commit()
        flash("Appointment requested! You will be notified once confirmed.", "success")
        return redirect(url_for("patient.dashboard"))

    # GET
    departments = db.execute("SELECT * FROM departments").fetchall()
    doctors = db.execute(
        "SELECT d.*, dept.name AS dept_name FROM doctors d "
        "LEFT JOIN departments dept ON d.department_id = dept.id"
    ).fetchall()
    return render_template("appointment/book.html", departments=departments, doctors=doctors)


@appointment_bp.route("/cancel/<int:id>", methods=["POST"])
def cancel(id):
    if not login_required():
        return redirect(url_for("auth.login"))

    db = get_db()
    db.execute(
        "UPDATE appointments SET status = 'cancelled' WHERE id = ? AND patient_id = ?",
        (id, session["user_id"]),
    )
    db.commit()
    flash("Appointment cancelled.", "info")
    return redirect(url_for("patient.dashboard"))