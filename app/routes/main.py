"""Main / home routes."""
from flask import Blueprint, render_template, Response
from app.routes.db import get_db


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    db = get_db()
    stats = {
        "doctors":      db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0],
        "patients":     db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
        "appointments": db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        "departments":  db.execute("SELECT COUNT(*) FROM departments").fetchone()[0],
    }
    departments = db.execute("SELECT * FROM departments").fetchall()
    doctors = db.execute(
        "SELECT d.*, dept.name AS dept_name "
        "FROM doctors d "
        "LEFT JOIN departments dept ON d.department_id = dept.id "
        "LIMIT 6"
    ).fetchall()
    return render_template(
        "index.html",
        stats=stats,
        departments=departments,
        doctors=doctors,
    )


@main_bp.route("/favicon.ico")
def favicon():
    return Response(status=204)