# 🏥 Smart Hospital Management System

A Flask-based web application to manage hospital operations including patients, doctors, appointments, prescriptions, and billing.

---

## 🚀 Features

### 👤 Patient
- Register & Login
- Book appointments
- View dashboard
- View prescriptions
- Manage profile

### 👨‍⚕️ Doctor
- View appointments
- Add prescriptions
- Manage patient records

### 👨‍💼 Admin
- Manage doctors & departments
- Monitor system activity

### 📅 Appointment System
- Book and manage appointments
- Status tracking

### 💊 Prescription System
- Doctors add prescriptions
- Patients view prescriptions

### 💳 Billing
- Generate billing records
- Track payments

---

## 🏗️ Project Structure

medicare/
│
├── app/
│   ├── __init__.py
│   ├── routes/
│   │    ├── auth.py
│   │    ├── patient.py
│   │    ├── doctor.py
│   │    ├── appointment.py
│   │    ├── billing.py
│   │    ├── db.py
│   │
│   ├── templates/
│   ├── static/
│
├── instance/
│   └── hospital.db
│
├── config.py
├── run.py
├── wsgi.py
├── requirements.txt
└── .env

---

## ⚙️ Installation

### 1. Clone repo
git clone <your-repo-url>
cd medicare

### 2. Create virtual environment
python -m venv venv

Activate:
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

---

### 3. Install dependencies
pip install -r requirements.txt

---

### 4. Setup environment variables

Create `.env` file:

SECRET_KEY=your_secret_key
DATABASE_PATH=instance/hospital.db
FLASK_ENV=development

---

## ▶️ Run Project

python run.py

App runs at:
http://127.0.0.1:5000

---

## 🧪 Default Login

### Admin
admin@hospital.com / admin123

### Doctor
sarah@hospital.com / doc123

### Patient
alice@patient.com / pat123

---



## 🔐 Security

- Password hashing
- Session-based authentication
- Role-based access
- CSRF protection (recommended)

---

## 🛠️ Tech Stack

- Backend: Flask (Python)
- Database: SQLite (dev), PostgreSQL (recommended)
- Frontend: HTML, CSS, Jinja2
- Server: Gunicorn

---

## 🔄 System Flow

Login → Dashboard → Book Appointment → Doctor → Prescription → Patient → Billing

---

## 📌 Future Improvements

- REST API
- JWT Authentication
- Payment Gateway
- PDF prescriptions
- Admin analytics

---

## 📄 License

For educational use.

---

## 👨‍💻 Author

Smart Hospital Management System Project
  
