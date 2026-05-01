"""
Smart Hospital Management System - Application Factory
"""
import os
import sqlite3
from flask import Flask
from werkzeug.security import generate_password_hash


class Config:
    SECRET_KEY    = os.environ.get("SECRET_KEY") or os.urandom(32)
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "..", "hospital.db")
    DEBUG         = os.environ.get("FLASK_DEBUG", "false").lower() == "true"


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    init_db(app)

    from app.routes.db import init_app as register_db_teardown
    register_db_teardown(app)

    from app.routes.main        import main_bp
    from app.routes.auth        import auth_bp
    from app.routes.admin       import admin_bp
    from app.routes.doctor      import doctor_bp # type: ignore
    from app.routes.patient import patient_bp# type: ignore
    from app.routes.appointment import appointment_bp # type: ignore
    from app.routes.billing     import billing_bp # type: ignore
    from app.routes.symptom     import symptom_bp # type: ignore

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,        url_prefix="/auth")
    app.register_blueprint(admin_bp,       url_prefix="/admin")
    app.register_blueprint(doctor_bp,      url_prefix="/doctor")
    app.register_blueprint(patient_bp, url_prefix="/patient")
    app.register_blueprint(appointment_bp, url_prefix="/appointment")
    app.register_blueprint(billing_bp,     url_prefix="/billing")
    app.register_blueprint(symptom_bp,     url_prefix="/symptom-checker")

    return app


# ── Database ──────────────────────────────────────────────────────────────────

def init_db(app):
    db_path = app.config["DATABASE_PATH"]
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")
        _create_schema(c)
        conn.commit()
        if _seed_required(c):
            _seed_data(c)
            conn.commit()


def _create_schema(c):
    c.execute("""CREATE TABLE IF NOT EXISTS departments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL UNIQUE,
        description TEXT,
        icon        TEXT DEFAULT 'fa-hospital'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS doctors (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        name           TEXT NOT NULL,
        email          TEXT UNIQUE NOT NULL,
        password       TEXT NOT NULL,
        phone          TEXT,
        specialization TEXT,
        department_id  INTEGER,
        experience     INTEGER DEFAULT 0,
        qualification  TEXT,
        fee            REAL    DEFAULT 500,
        avatar         TEXT    DEFAULT 'default_doctor.png',
        available_days TEXT    DEFAULT 'Mon,Tue,Wed,Thu,Fri',
        status         TEXT    DEFAULT 'active',
        created_at     TEXT    DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS patients (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        phone       TEXT,
        dob         TEXT,
        gender      TEXT,
        blood_group TEXT,
        address     TEXT,
        avatar      TEXT DEFAULT 'default_patient.png',
        status      TEXT DEFAULT 'active',
        created_at  TEXT DEFAULT (CURRENT_TIMESTAMP)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS appointments (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id  INTEGER NOT NULL,
        date       TEXT    NOT NULL,
        time_slot  TEXT    NOT NULL,
        reason     TEXT,
        status     TEXT DEFAULT 'pending',
        notes      TEXT,
        created_at TEXT DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS medical_records (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id     INTEGER NOT NULL,
        doctor_id      INTEGER NOT NULL,
        appointment_id INTEGER,
        diagnosis      TEXT,
        prescription   TEXT,
        notes          TEXT,
        report_file    TEXT,
        created_at     TEXT DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (patient_id)     REFERENCES patients(id),
        FOREIGN KEY (doctor_id)      REFERENCES doctors(id),
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lab_tests (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        test_name  TEXT    NOT NULL,
        test_date  TEXT,
        result     TEXT,
        status     TEXT DEFAULT 'pending',
        cost       REAL DEFAULT 0,
        created_at TEXT DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS billing (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id     INTEGER NOT NULL,
        appointment_id INTEGER,
        amount         REAL NOT NULL DEFAULT 0,
        discount       REAL DEFAULT 0,
        tax            REAL DEFAULT 0,
        total          REAL NOT NULL DEFAULT 0,
        payment_method TEXT DEFAULT 'cash',
        payment_status TEXT DEFAULT 'pending',
        description    TEXT,
        created_at     TEXT DEFAULT (CURRENT_TIMESTAMP),
        FOREIGN KEY (patient_id)     REFERENCES patients(id),
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS admins (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        email      TEXT UNIQUE NOT NULL,
        password   TEXT NOT NULL,
        created_at TEXT DEFAULT (CURRENT_TIMESTAMP)
    )""")


def _seed_required(c):
    c.execute("SELECT COUNT(*) FROM admins")
    return c.fetchone()[0] == 0


def _seed_data(c):
    c.executemany(
        "INSERT OR IGNORE INTO departments (name, description, icon) VALUES (?,?,?)",
        [
            ("Cardiology",      "Heart & cardiovascular diseases",      "fa-heart"),
            ("Neurology",       "Brain & nervous system disorders",     "fa-brain"),
            ("Orthopedics",     "Bone, joint & muscle conditions",      "fa-bone"),
            ("Pediatrics",      "Child health & development",           "fa-baby"),
            ("Dermatology",     "Skin, hair & nail disorders",          "fa-allergies"),
            ("Ophthalmology",   "Eye care & vision disorders",          "fa-eye"),
            ("General Surgery", "Surgical treatments & procedures",     "fa-procedures"),
            ("Gynecology",      "Women health & reproductive medicine", "fa-venus"),
        ],
    )
    c.execute(
        "INSERT OR IGNORE INTO admins (name, email, password) VALUES (?,?,?)",
        ("Admin", "admin@hospital.com", generate_password_hash("admin123")),
    )
    c.executemany(
        """INSERT OR IGNORE INTO doctors
           (name,email,password,phone,specialization,department_id,experience,qualification,fee)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            ("Dr. Sarah Johnson",   "sarah@hospital.com",   generate_password_hash("doc123"),
             "9876543210", "Cardiologist",    1, 12, "MD, FACC",  800),
            ("Dr. Michael Chen",    "michael@hospital.com", generate_password_hash("doc123"),
             "9876543211", "Neurologist",     2, 15, "MD, PhD",   900),
            ("Dr. Emily Davis",     "emily@hospital.com",   generate_password_hash("doc123"),
             "9876543212", "Orthopedic",      3,  8, "MS Ortho",  750),
            ("Dr. James Wilson",    "james@hospital.com",   generate_password_hash("doc123"),
             "9876543213", "Pediatrician",    4, 10, "MD Paeds",  600),
            ("Dr. Priya Sharma",    "priya@hospital.com",   generate_password_hash("doc123"),
             "9876543214", "Dermatologist",   5,  6, "MD Derma",  700),
            ("Dr. Robert Martinez", "robert@hospital.com",  generate_password_hash("doc123"),
             "9876543215", "Ophthalmologist", 6, 14, "MS Ophtha", 650),
        ],
    )
    c.executemany(
        """INSERT OR IGNORE INTO patients
           (name,email,password,phone,dob,gender,blood_group,address)
           VALUES (?,?,?,?,?,?,?,?)""",
        [
            ("Alice Martin", "alice@patient.com", generate_password_hash("pat123"),
             "9123456780", "1990-05-14", "Female", "A+",  "123 Oak Street"),
            ("Bob Thompson", "bob@patient.com",   generate_password_hash("pat123"),
             "9123456781", "1985-08-22", "Male",   "O+",  "456 Pine Avenue"),
            ("Carol White",  "carol@patient.com", generate_password_hash("pat123"),
             "9123456782", "1995-11-30", "Female", "B-",  "789 Maple Drive"),
            ("David Harris", "david@patient.com", generate_password_hash("pat123"),
             "9123456783", "1978-03-17", "Male",   "AB+", "321 Elm Road"),
        ],
    )
    c.executemany(
        "INSERT INTO appointments (patient_id,doctor_id,date,time_slot,reason,status) VALUES (?,?,?,?,?,?)",
        [
            (1, 1, "2025-03-20", "09:00 AM", "Chest pain follow-up",   "confirmed"),
            (2, 2, "2025-03-21", "10:30 AM", "Headache & dizziness",   "confirmed"),
            (3, 3, "2025-03-22", "11:00 AM", "Knee pain consultation", "pending"),
            (4, 4, "2025-03-23", "02:00 PM", "Child vaccination",      "confirmed"),
            (1, 5, "2025-03-24", "03:30 PM", "Skin allergy review",    "pending"),
            (2, 6, "2025-03-25", "04:00 PM", "Eye check-up",           "confirmed"),
        ],
    )
    c.executemany(
        """INSERT INTO billing
           (patient_id,appointment_id,amount,discount,tax,total,payment_method,payment_status,description)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        [
            (1, 1, 800, 50,    30,    780,    "card", "paid",    "Cardiology Consultation"),
            (2, 2, 900,  0,    45,    945,    "cash", "paid",    "Neurology Consultation"),
            (3, 3, 750, 75,    33.75, 708.75, "upi",  "pending", "Orthopedic Consultation"),
            (4, 4, 600,  0,    30,    630,    "cash", "paid",    "Pediatric Consultation"),
        ],
    )
    c.executemany(
        "INSERT INTO lab_tests (patient_id,test_name,test_date,result,status,cost) VALUES (?,?,?,?,?,?)",
        [
            (1, "Complete Blood Count", "2025-03-18", "Normal range",   "completed", 350),
            (2, "MRI Brain Scan",       "2025-03-19", "No abnormality", "completed", 2500),
            (3, "X-Ray Knee",           "2025-03-20", "Pending review", "pending",   800),
            (4, "Blood Sugar Test",     "2025-03-21", "95 mg/dL",       "completed", 200),
        ],
    )
