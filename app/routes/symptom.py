"""Symptom checker routes."""
from flask import Blueprint, render_template, request
from app.routes.db import get_db

symptom_bp = Blueprint("symptom", __name__)


# Simple symptom → department mapping
SYMPTOM_MAP = [
    ("chest pain, heart, breath, heart attack, palpitation", "cardiology",  "Cardiology"),
    ("headache, migraine, neuro, brain, seizure, memory",     "neurology",   "Neurology"),
    ("bone, joint, fracture, back pain, spine, ortho",         "orthopedics", "Orthopedics"),
    ("skin, rash, allergy, eczema, acne, hair",               "dermatology", "Dermatology"),
    ("kidney, urine, bladder, stone, prostate",                "urology",     "Urology"),
    ("stomach, liver, digestion, gastro, acid, vomiting",      "gastroenterology", "Gastroenterology"),
    ("eye, vision, cataract, retina, glasses",                "ophthalmology", "Ophthalmology"),
    ("child, baby, pediatric, kids, infant",                   "pediatrics",  "Pediatrics"),
    ("teeth, tooth, gum, dental, cavity",                      "dentistry",   "Dentistry"),
    ("general, fever, cold, flu, checkup, routine",            None,          "General Medicine"),
]


def _match(text):
    text = text.lower()
    for keywords, _, name in SYMPTOM_MAP:
        if any(kw in text for kw in keywords.split(", ")):
            return name
    return "General Medicine"


@symptom_bp.route("/")
def index():
    departments = None
    suggested   = None
    query       = ""

    query = request.args.get("q", "").strip()

    if query:
        suggested = _match(query)
        db = get_db()
        departments = db.execute(
            """SELECT d.*, dept.name AS dept_name
               FROM doctors d
               LEFT JOIN departments dept ON d.department_id = dept.id
               WHERE dept.name LIKE ? LIMIT 6""",
            (f"%{suggested}%",),
        ).fetchall()

    return render_template(
        "symptom/index.html",
        departments=departments,
        suggested=suggested,
        query=query,
    )