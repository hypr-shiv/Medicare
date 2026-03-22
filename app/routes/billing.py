"""Billing routes."""
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, request
)
from app.routes.db import get_db

billing_bp = Blueprint("billing", __name__)


@billing_bp.route("/pay/<int:appointment_id>", methods=["GET", "POST"])
def pay(appointment_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()

    if request.method == "POST":
        amount   = request.form.get("amount", 0)
        method   = request.form.get("method", "cash")
        patient_id = session["user_id"]

        db.execute(
            """INSERT INTO billing
               (appointment_id, patient_id, amount, total, payment_method, payment_status)
               VALUES (?, ?, ?, ?, ?, 'paid')""",
            (appointment_id, patient_id, amount, amount, method),
        )
        db.execute(
            "UPDATE appointments SET status = 'completed' WHERE id = ?",
            (appointment_id,),
        )
        db.commit()
        flash("Payment successful!", "success")
        return redirect(url_for("patient.dashboard"))

    # GET
    appointment = db.execute(
        """SELECT a.*, d.name AS doctor_name, d.fee
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           WHERE a.id = ? AND a.patient_id = ?""",
        (appointment_id, session["user_id"]),
    ).fetchone()

    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("patient.dashboard"))

    return render_template("billing/pay.html", appointment=appointment)


@billing_bp.route("/history")
def history():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = get_db()
    bills = db.execute(
        """SELECT b.*, a.date AS appt_date, d.name AS doctor_name
           FROM billing b
           JOIN appointments a ON b.appointment_id = a.id
           JOIN doctors d ON a.doctor_id = d.id
           WHERE b.patient_id = ?
           ORDER BY b.created_at DESC""",
        (session["user_id"],),
    ).fetchall()
    return render_template("billing/history.html", bills=bills)