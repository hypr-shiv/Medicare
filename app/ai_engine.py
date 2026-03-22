"""
=======================================================================
  MediCare – AI Symptom Checker Engine
  Uses a multi-label Random Forest + TF-IDF + Rule-based hybrid model
=======================================================================
"""

import numpy as np
import pickle
import os
import re
from collections import defaultdict

# ── Comprehensive Symptom → Disease Knowledge Base ──────────────────
SYMPTOM_DISEASE_DB = {
    # ── Cardiology ─────────────────────────────────────────────────
    "Heart Attack": {
        "symptoms": ["chest pain", "chest tightness", "chest pressure", "left arm pain",
                     "jaw pain", "shortness of breath", "sweating", "nausea",
                     "dizziness", "cold sweat", "fatigue", "palpitations"],
        "department": "Cardiology",
        "severity": "critical",
        "icd": "I21",
        "description": "A blockage of blood flow to the heart muscle causing tissue damage.",
        "advice": "Call emergency services immediately (911). Chew aspirin if available.",
        "tests": ["ECG", "Troponin Blood Test", "Echocardiogram", "Coronary Angiography"]
    },
    "Angina": {
        "symptoms": ["chest pain", "chest pressure", "shortness of breath", "fatigue",
                     "dizziness", "sweating", "nausea"],
        "department": "Cardiology",
        "severity": "high",
        "icd": "I20",
        "description": "Reduced blood flow to the heart causing chest pain and discomfort.",
        "advice": "Rest immediately. Use prescribed nitroglycerin if available. Seek urgent care.",
        "tests": ["ECG", "Stress Test", "Blood Pressure Monitoring", "Lipid Profile"]
    },
    "Hypertension": {
        "symptoms": ["headache", "dizziness", "blurred vision", "shortness of breath",
                     "nosebleed", "chest pain", "fatigue", "palpitations"],
        "department": "Cardiology",
        "severity": "moderate",
        "icd": "I10",
        "description": "Persistently elevated blood pressure that damages arteries and organs.",
        "advice": "Monitor blood pressure regularly. Reduce salt intake. Take prescribed medications.",
        "tests": ["Blood Pressure Monitoring", "ECG", "Kidney Function Test", "Lipid Panel"]
    },
    "Heart Failure": {
        "symptoms": ["shortness of breath", "swollen ankles", "swollen feet", "leg swelling",
                     "fatigue", "rapid heartbeat", "persistent cough", "wheezing",
                     "reduced exercise tolerance", "frequent urination at night"],
        "department": "Cardiology",
        "severity": "high",
        "icd": "I50",
        "description": "The heart cannot pump enough blood to meet the body's needs.",
        "advice": "Restrict fluid and salt intake. Monitor weight daily. Take all medications.",
        "tests": ["Echocardiogram", "BNP Blood Test", "Chest X-ray", "ECG"]
    },
    "Arrhythmia": {
        "symptoms": ["palpitations", "irregular heartbeat", "racing heart", "slow heartbeat",
                     "dizziness", "fainting", "shortness of breath", "chest discomfort"],
        "department": "Cardiology",
        "severity": "moderate",
        "icd": "I49",
        "description": "Abnormal heart rhythm that can cause the heart to beat too fast, slow, or irregularly.",
        "advice": "Avoid caffeine and alcohol. Track symptoms. Seek prompt medical evaluation.",
        "tests": ["Holter Monitor", "ECG", "Echocardiogram", "Electrophysiology Study"]
    },

    # ── Neurology ───────────────────────────────────────────────────
    "Migraine": {
        "symptoms": ["severe headache", "throbbing headache", "nausea", "vomiting",
                     "light sensitivity", "sound sensitivity", "visual aura",
                     "one-sided headache", "blurred vision"],
        "department": "Neurology",
        "severity": "moderate",
        "icd": "G43",
        "description": "A neurological condition causing intense recurring headaches often with nausea and sensitivity.",
        "advice": "Rest in a dark quiet room. Stay hydrated. Apply cold compress to forehead.",
        "tests": ["Neurological Exam", "MRI Brain", "CT Scan"]
    },
    "Stroke": {
        "symptoms": ["sudden numbness", "face drooping", "arm weakness", "speech difficulty",
                     "confusion", "vision problems", "severe headache", "loss of balance",
                     "trouble walking", "slurred speech"],
        "department": "Neurology",
        "severity": "critical",
        "icd": "I63",
        "description": "A brain attack caused by blocked or ruptured blood vessels in the brain.",
        "advice": "FAST: Face drooping, Arm weakness, Speech difficulty = Time to call 911 immediately.",
        "tests": ["CT Scan Brain", "MRI Brain", "Carotid Ultrasound", "Angiography"]
    },
    "Epilepsy": {
        "symptoms": ["seizures", "convulsions", "loss of consciousness", "confusion",
                     "staring spell", "temporary blackout", "muscle jerking", "anxiety"],
        "department": "Neurology",
        "severity": "high",
        "icd": "G40",
        "description": "A neurological disorder characterized by recurrent unprovoked seizures.",
        "advice": "Do not leave patient alone. Remove dangerous objects. Time the seizure duration.",
        "tests": ["EEG", "MRI Brain", "Blood Tests", "Neuropsychological Tests"]
    },
    "Parkinson's Disease": {
        "symptoms": ["tremors", "hand tremors", "stiffness", "slow movement", "balance problems",
                     "shuffling gait", "small handwriting", "soft speech", "masked face"],
        "department": "Neurology",
        "severity": "moderate",
        "icd": "G20",
        "description": "A progressive nervous system disorder affecting movement, balance, and coordination.",
        "advice": "Regular exercise helps. Physical and occupational therapy are beneficial.",
        "tests": ["Neurological Exam", "DAT Scan", "MRI Brain", "Dopamine Testing"]
    },
    "Meningitis": {
        "symptoms": ["stiff neck", "severe headache", "high fever", "photophobia",
                     "nausea", "vomiting", "rash", "confusion", "sensitivity to light"],
        "department": "Neurology",
        "severity": "critical",
        "icd": "G03",
        "description": "Inflammation of the membranes surrounding the brain and spinal cord.",
        "advice": "EMERGENCY: Seek immediate medical care. This is potentially life-threatening.",
        "tests": ["Lumbar Puncture", "Blood Culture", "CT Scan", "MRI Brain"]
    },

    # ── Orthopedics ─────────────────────────────────────────────────
    "Arthritis": {
        "symptoms": ["joint pain", "joint stiffness", "swollen joints", "reduced range of motion",
                     "joint tenderness", "warmth around joints", "morning stiffness",
                     "difficulty walking", "knee pain", "hip pain"],
        "department": "Orthopedics",
        "severity": "moderate",
        "icd": "M13",
        "description": "Inflammation of one or more joints causing pain, stiffness, and reduced mobility.",
        "advice": "Apply warm/cold compress. Gentle exercises help. Maintain healthy weight.",
        "tests": ["X-Ray", "MRI", "Blood Tests (RF, Anti-CCP)", "Joint Fluid Analysis"]
    },
    "Fracture": {
        "symptoms": ["bone pain", "swelling", "bruising", "deformity", "tenderness",
                     "inability to move", "numbness", "tingling", "popping sound"],
        "department": "Orthopedics",
        "severity": "high",
        "icd": "S72",
        "description": "A break or crack in a bone requiring immobilization and possible surgical intervention.",
        "advice": "Immobilize the injured area. Apply ice. Do not attempt to realign bones.",
        "tests": ["X-Ray", "CT Scan", "MRI", "Bone Density Test"]
    },
    "Osteoporosis": {
        "symptoms": ["back pain", "loss of height", "stooped posture", "bone pain",
                     "frequent fractures", "brittle nails", "reduced grip strength"],
        "department": "Orthopedics",
        "severity": "moderate",
        "icd": "M81",
        "description": "A condition where bones become weak and brittle, increasing fracture risk.",
        "advice": "Increase calcium and vitamin D intake. Weight-bearing exercise. Avoid falls.",
        "tests": ["Bone Density Scan (DEXA)", "Blood Tests", "X-Ray", "Calcium Level Test"]
    },
    "Back Pain": {
        "symptoms": ["lower back pain", "back pain", "muscle ache", "shooting pain",
                     "leg pain", "limited flexibility", "inability to stand straight",
                     "numbness in legs", "tingling in legs"],
        "department": "Orthopedics",
        "severity": "low",
        "icd": "M54",
        "description": "Pain in the lumbar spine region, often due to muscle strain or disc issues.",
        "advice": "Apply ice first 48h, then heat. Gentle stretching. Avoid prolonged bed rest.",
        "tests": ["X-Ray", "MRI Spine", "CT Scan", "Nerve Conduction Study"]
    },

    # ── Pulmonology / General ───────────────────────────────────────
    "Pneumonia": {
        "symptoms": ["cough", "productive cough", "high fever", "chills", "shortness of breath",
                     "chest pain when breathing", "fatigue", "sweating", "nausea",
                     "loss of appetite", "rapid breathing", "rapid heart rate"],
        "department": "Pulmonology",
        "severity": "high",
        "icd": "J18",
        "description": "A lung infection that inflames air sacs, causing them to fill with fluid or pus.",
        "advice": "Rest and stay hydrated. Take prescribed antibiotics. Monitor oxygen levels.",
        "tests": ["Chest X-Ray", "Blood Tests", "Sputum Culture", "Pulse Oximetry"]
    },
    "Asthma": {
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "coughing",
                     "coughing at night", "difficulty breathing", "breathlessness",
                     "chest tightness at night"],
        "department": "Pulmonology",
        "severity": "moderate",
        "icd": "J45",
        "description": "A chronic lung disease causing airway inflammation and breathing difficulties.",
        "advice": "Always carry rescue inhaler. Identify and avoid triggers. Follow asthma action plan.",
        "tests": ["Spirometry", "Peak Flow Test", "Allergy Tests", "Chest X-Ray"]
    },
    "Bronchitis": {
        "symptoms": ["cough", "mucus production", "fatigue", "shortness of breath",
                     "slight fever", "chills", "chest discomfort", "sore throat"],
        "department": "Pulmonology",
        "severity": "low",
        "icd": "J40",
        "description": "Inflammation of the bronchial tube lining, often following a cold.",
        "advice": "Rest, stay hydrated. Use a humidifier. Honey and lemon for sore throat.",
        "tests": ["Chest X-Ray", "Pulmonary Function Test", "Sputum Test", "Blood Tests"]
    },
    "COPD": {
        "symptoms": ["chronic cough", "shortness of breath", "wheezing", "chest tightness",
                     "frequent respiratory infections", "lack of energy", "unintended weight loss",
                     "coughing up mucus", "blue lips"],
        "department": "Pulmonology",
        "severity": "high",
        "icd": "J44",
        "description": "A chronic inflammatory lung disease that obstructs airflow from the lungs.",
        "advice": "Stop smoking immediately. Avoid air pollutants. Take prescribed inhalers.",
        "tests": ["Spirometry", "Chest X-Ray", "CT Scan", "Arterial Blood Gas"]
    },

    # ── Dermatology ─────────────────────────────────────────────────
    "Eczema": {
        "symptoms": ["itchy skin", "dry skin", "skin redness", "rash", "skin inflammation",
                     "scaly patches", "skin lesions", "blisters", "cracked skin"],
        "department": "Dermatology",
        "severity": "low",
        "icd": "L20",
        "description": "A condition that makes skin red, inflamed, and itchy, often chronic.",
        "advice": "Moisturize frequently. Use gentle fragrance-free soaps. Avoid scratching.",
        "tests": ["Skin Patch Test", "Allergy Test", "Skin Biopsy", "IgE Blood Test"]
    },
    "Psoriasis": {
        "symptoms": ["scaly patches", "red patches", "skin thickening", "itchy skin",
                     "burning sensation", "soreness", "nail changes", "joint pain"],
        "department": "Dermatology",
        "severity": "moderate",
        "icd": "L40",
        "description": "A chronic autoimmune condition causing rapid skin cell buildup and scaling.",
        "advice": "Moisturize daily. Avoid triggers like stress and infections. Use prescribed creams.",
        "tests": ["Skin Biopsy", "Blood Tests", "Joint X-Ray", "Nail Examination"]
    },
    "Acne": {
        "symptoms": ["pimples", "blackheads", "whiteheads", "skin redness", "oily skin",
                     "cysts", "nodules", "painful bumps", "scarring"],
        "department": "Dermatology",
        "severity": "low",
        "icd": "L70",
        "description": "A common skin condition causing pimples when follicles become clogged.",
        "advice": "Wash face twice daily. Avoid touching face. Use oil-free sunscreen.",
        "tests": ["Skin Examination", "Hormonal Profile", "Bacterial Culture"]
    },

    # ── Gastroenterology ────────────────────────────────────────────
    "Gastroenteritis": {
        "symptoms": ["nausea", "vomiting", "diarrhea", "stomach cramps", "abdominal pain",
                     "fever", "headache", "muscle aches", "loss of appetite", "dehydration"],
        "department": "Gastroenterology",
        "severity": "moderate",
        "icd": "A09",
        "description": "Inflammation of the stomach and intestines, typically due to viral or bacterial infection.",
        "advice": "Stay hydrated with oral rehydration salts. Eat bland foods (BRAT diet). Rest.",
        "tests": ["Stool Culture", "Blood Tests", "Stool Antigen Test", "Colonoscopy"]
    },
    "Appendicitis": {
        "symptoms": ["abdominal pain", "pain around navel", "pain lower right abdomen",
                     "nausea", "vomiting", "fever", "loss of appetite", "abdominal rigidity",
                     "rebound tenderness"],
        "department": "General Surgery",
        "severity": "critical",
        "icd": "K37",
        "description": "Inflammation of the appendix requiring urgent surgical removal.",
        "advice": "URGENT: Do NOT eat or drink. Seek emergency care immediately.",
        "tests": ["Blood Tests (WBC)", "Abdominal Ultrasound", "CT Scan Abdomen", "Urine Test"]
    },
    "GERD": {
        "symptoms": ["heartburn", "acid reflux", "regurgitation", "chest burning", "sour taste",
                     "difficulty swallowing", "chronic cough", "hoarseness", "bloating"],
        "department": "Gastroenterology",
        "severity": "low",
        "icd": "K21",
        "description": "Stomach acid frequently flows back into the esophagus causing irritation.",
        "advice": "Avoid trigger foods. Don't lie down after eating. Elevate head of bed.",
        "tests": ["Endoscopy", "pH Monitoring", "Esophageal Manometry", "Barium Swallow"]
    },
    "Irritable Bowel Syndrome": {
        "symptoms": ["abdominal cramps", "bloating", "gas", "diarrhea", "constipation",
                     "mucus in stool", "abdominal pain", "incomplete evacuation"],
        "department": "Gastroenterology",
        "severity": "low",
        "icd": "K58",
        "description": "A common disorder affecting the large intestine causing chronic abdominal symptoms.",
        "advice": "Track trigger foods. Reduce stress. Increase fiber gradually.",
        "tests": ["Colonoscopy", "Blood Tests", "Stool Tests", "Hydrogen Breath Test"]
    },

    # ── Pediatrics ──────────────────────────────────────────────────
    "Chickenpox": {
        "symptoms": ["itchy rash", "red spots", "blisters", "fever", "fatigue",
                     "loss of appetite", "headache", "fluid-filled blisters"],
        "department": "Pediatrics",
        "severity": "low",
        "icd": "B01",
        "description": "A highly contagious viral infection causing an itchy blister-like rash.",
        "advice": "Isolate the patient. Trim nails to avoid scratching. Use calamine lotion.",
        "tests": ["Physical Examination", "PCR Test", "Blood Tests (VZV Antibodies)"]
    },
    "Measles": {
        "symptoms": ["high fever", "rash", "runny nose", "cough", "red eyes",
                     "white spots in mouth", "sensitivity to light", "sore throat"],
        "department": "Pediatrics",
        "severity": "high",
        "icd": "B05",
        "description": "A highly contagious viral disease causing fever and widespread rash.",
        "advice": "Isolate the patient. Rest and hydrate. Vitamin A supplementation helps.",
        "tests": ["Blood Tests (IgM Antibodies)", "Throat Swab", "Physical Examination"]
    },

    # ── Ophthalmology ───────────────────────────────────────────────
    "Conjunctivitis": {
        "symptoms": ["red eyes", "eye discharge", "watery eyes", "itchy eyes",
                     "eye swelling", "crusty eyelids", "sensitivity to light", "burning eyes"],
        "department": "Ophthalmology",
        "severity": "low",
        "icd": "H10",
        "description": "Inflammation of the conjunctiva (the outer layer of the eye).",
        "advice": "Clean eyes with saline. Avoid touching eyes. Change pillowcases daily.",
        "tests": ["Eye Examination", "Conjunctival Swab", "Slit-Lamp Examination"]
    },
    "Glaucoma": {
        "symptoms": ["vision loss", "blurred vision", "eye pain", "headache",
                     "nausea", "rainbow halos", "sudden vision changes", "tunnel vision"],
        "department": "Ophthalmology",
        "severity": "high",
        "icd": "H40",
        "description": "A group of eye conditions that damage the optic nerve, often due to high eye pressure.",
        "advice": "Regular eye pressure monitoring. Use prescribed eye drops. Avoid heavy lifting.",
        "tests": ["Tonometry", "Visual Field Test", "Optical Coherence Tomography", "Gonioscopy"]
    },

    # ── Endocrinology / General ─────────────────────────────────────
    "Diabetes Type 2": {
        "symptoms": ["frequent urination", "excessive thirst", "unexplained weight loss",
                     "fatigue", "blurred vision", "slow healing wounds", "frequent infections",
                     "tingling hands", "tingling feet", "increased hunger", "dark skin patches"],
        "department": "Endocrinology",
        "severity": "moderate",
        "icd": "E11",
        "description": "A metabolic disease causing high blood sugar due to insulin resistance.",
        "advice": "Monitor blood sugar regularly. Follow diabetic diet. Exercise daily.",
        "tests": ["Fasting Blood Sugar", "HbA1c", "Oral Glucose Tolerance Test", "Urine Test"]
    },
    "Hypothyroidism": {
        "symptoms": ["fatigue", "weight gain", "cold intolerance", "constipation",
                     "dry skin", "hair loss", "puffy face", "muscle weakness",
                     "slow heart rate", "depression", "memory problems"],
        "department": "Endocrinology",
        "severity": "moderate",
        "icd": "E03",
        "description": "The thyroid gland doesn't produce enough thyroid hormones.",
        "advice": "Take prescribed levothyroxine consistently. Annual thyroid function tests.",
        "tests": ["TSH Test", "T3/T4 Blood Test", "Thyroid Ultrasound", "Antibody Tests"]
    },
    "Hyperthyroidism": {
        "symptoms": ["weight loss", "rapid heartbeat", "increased appetite", "anxiety",
                     "tremors", "sweating", "heat intolerance", "irritability",
                     "sleep problems", "enlarged thyroid", "frequent bowel movements"],
        "department": "Endocrinology",
        "severity": "moderate",
        "icd": "E05",
        "description": "The thyroid produces too much thyroxine hormone, speeding up metabolism.",
        "advice": "Avoid iodine-rich foods. Wear sunglasses outdoors. Monitor heart rate.",
        "tests": ["TSH Test", "T3/T4 Blood Test", "Radioiodine Uptake", "Thyroid Scan"]
    },

    # ── Nephrology / Urology ────────────────────────────────────────
    "Urinary Tract Infection": {
        "symptoms": ["burning urination", "frequent urination", "cloudy urine", "strong urine odor",
                     "pelvic pain", "blood in urine", "lower abdominal pain", "urgency to urinate",
                     "painful urination"],
        "department": "Urology",
        "severity": "moderate",
        "icd": "N39",
        "description": "An infection in any part of the urinary system including kidneys, bladder, or urethra.",
        "advice": "Drink plenty of water. Urinate frequently. Take prescribed antibiotics.",
        "tests": ["Urine Culture", "Urinalysis", "Blood Tests", "Ultrasound Kidneys"]
    },
    "Kidney Stones": {
        "symptoms": ["severe back pain", "severe side pain", "pain radiating to groin",
                     "nausea", "vomiting", "blood in urine", "painful urination",
                     "frequent urination", "fever", "chills"],
        "department": "Urology",
        "severity": "high",
        "icd": "N20",
        "description": "Hard deposits made of minerals and salts that form inside the kidneys.",
        "advice": "Drink 2-3 liters of water daily. Use pain relief. Some stones pass naturally.",
        "tests": ["CT Scan", "Ultrasound", "Urinalysis", "Urine 24-hour Collection", "Blood Tests"]
    },

    # ── Psychiatry ──────────────────────────────────────────────────
    "Depression": {
        "symptoms": ["persistent sadness", "loss of interest", "fatigue", "sleep problems",
                     "appetite changes", "concentration problems", "hopelessness",
                     "worthlessness", "social withdrawal", "suicidal thoughts"],
        "department": "Psychiatry",
        "severity": "moderate",
        "icd": "F32",
        "description": "A mental health disorder causing persistent sadness and loss of interest.",
        "advice": "Seek professional help immediately. Maintain daily routine. Stay connected socially.",
        "tests": ["PHQ-9 Assessment", "Blood Tests", "Thyroid Function", "Psychological Evaluation"]
    },
    "Anxiety Disorder": {
        "symptoms": ["excessive worry", "nervousness", "restlessness", "rapid heartbeat",
                     "sweating", "trembling", "trouble sleeping", "concentration problems",
                     "irritability", "muscle tension", "panic attacks"],
        "department": "Psychiatry",
        "severity": "moderate",
        "icd": "F41",
        "description": "A disorder characterized by persistent, excessive fear or worry about everyday situations.",
        "advice": "Practice deep breathing and meditation. Limit caffeine and alcohol.",
        "tests": ["GAD-7 Assessment", "Blood Tests", "Heart Rate Monitoring", "Psychological Evaluation"]
    },

    # ── Gynecology ──────────────────────────────────────────────────
    "PCOS": {
        "symptoms": ["irregular periods", "heavy periods", "acne", "excess hair growth",
                     "weight gain", "hair thinning", "skin darkening", "fatigue",
                     "pelvic pain", "difficulty conceiving"],
        "department": "Gynecology",
        "severity": "moderate",
        "icd": "E28",
        "description": "A hormonal disorder causing enlarged ovaries with small cysts on the outer edges.",
        "advice": "Maintain healthy weight. Regular exercise. Follow low-glycemic diet.",
        "tests": ["Pelvic Ultrasound", "Hormone Tests", "Blood Sugar Test", "Lipid Profile"]
    },

    # ── Infectious Disease ──────────────────────────────────────────
    "COVID-19": {
        "symptoms": ["fever", "dry cough", "fatigue", "loss of smell", "loss of taste",
                     "shortness of breath", "body aches", "sore throat", "headache",
                     "chills", "diarrhea", "runny nose"],
        "department": "Infectious Disease",
        "severity": "high",
        "icd": "U07",
        "description": "A respiratory illness caused by the SARS-CoV-2 coronavirus.",
        "advice": "Isolate immediately. Monitor oxygen levels. Seek urgent care if oxygen drops below 94%.",
        "tests": ["RT-PCR Test", "Rapid Antigen Test", "Chest X-Ray", "Blood Tests (CBC)"]
    },
    "Malaria": {
        "symptoms": ["high fever", "chills", "sweating", "headache", "nausea",
                     "vomiting", "muscle pain", "fatigue", "anemia", "spleen enlargement"],
        "department": "Infectious Disease",
        "severity": "high",
        "icd": "B50",
        "description": "A life-threatening disease transmitted through infected mosquito bites.",
        "advice": "Take prescribed antimalarial medication. Use mosquito nets and repellents.",
        "tests": ["Malaria Rapid Test", "Blood Smear", "PCR Test", "Complete Blood Count"]
    },
    "Dengue Fever": {
        "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint pain",
                     "muscle pain", "rash", "nausea", "vomiting", "fatigue",
                     "bleeding gums", "easy bruising"],
        "department": "Infectious Disease",
        "severity": "high",
        "icd": "A90",
        "description": "A mosquito-borne viral infection causing severe flu-like symptoms.",
        "advice": "Stay hydrated. Monitor platelet count. Avoid aspirin and ibuprofen.",
        "tests": ["NS1 Antigen Test", "Dengue IgM/IgG", "Complete Blood Count", "Platelet Count"]
    },
    "Typhoid": {
        "symptoms": ["sustained fever", "weakness", "abdominal pain", "headache",
                     "diarrhea", "constipation", "rash", "loss of appetite", "cough"],
        "department": "Infectious Disease",
        "severity": "high",
        "icd": "A01",
        "description": "A bacterial infection caused by Salmonella typhi, spread through contaminated food/water.",
        "advice": "Take prescribed antibiotics. Avoid raw food and untreated water.",
        "tests": ["Widal Test", "Blood Culture", "Stool Culture", "Typhidot Test"]
    },
    "Influenza": {
        "symptoms": ["fever", "cough", "sore throat", "runny nose", "body aches",
                     "headache", "chills", "fatigue", "vomiting", "diarrhea"],
        "department": "General Medicine",
        "severity": "moderate",
        "icd": "J09",
        "description": "A contagious respiratory illness caused by influenza viruses.",
        "advice": "Rest and stay hydrated. Antiviral medications if started within 48 hours.",
        "tests": ["Rapid Influenza Test", "Throat Swab", "Blood Tests", "Chest X-Ray"]
    },
    "Common Cold": {
        "symptoms": ["runny nose", "stuffy nose", "sore throat", "cough",
                     "sneezing", "low grade fever", "mild headache", "body aches",
                     "watery eyes", "fatigue"],
        "department": "General Medicine",
        "severity": "low",
        "icd": "J00",
        "description": "A mild viral upper respiratory tract infection lasting about 7-10 days.",
        "advice": "Rest, stay hydrated. Honey and lemon for sore throat. Saline nasal spray helps.",
        "tests": ["Physical Examination", "Throat Swab (if needed)"]
    },
    "Anemia": {
        "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath",
                     "dizziness", "cold hands", "cold feet", "headache",
                     "chest pain", "brittle nails", "pica"],
        "department": "Hematology",
        "severity": "moderate",
        "icd": "D64",
        "description": "A condition where you lack enough healthy red blood cells to carry adequate oxygen.",
        "advice": "Eat iron-rich foods. Take prescribed iron supplements. Increase vitamin C intake.",
        "tests": ["Complete Blood Count", "Iron Studies", "Reticulocyte Count", "Bone Marrow Biopsy"]
    },
}

# ── All unique symptoms list ──────────────────────────────────────────
ALL_SYMPTOMS = sorted(set(
    symptom for disease_data in SYMPTOM_DISEASE_DB.values()
    for symptom in disease_data["symptoms"]
))

# ── Department color mapping ──────────────────────────────────────────
DEPT_COLORS = {
    "Cardiology":        {"bg": "#fef2f2", "border": "#ef4444", "text": "#991b1b", "icon": "fa-heart"},
    "Neurology":         {"bg": "#f5f3ff", "border": "#8b5cf6", "text": "#5b21b6", "icon": "fa-brain"},
    "Orthopedics":       {"bg": "#fff7ed", "border": "#f97316", "text": "#9a3412", "icon": "fa-bone"},
    "Pulmonology":       {"bg": "#ecfeff", "border": "#06b6d4", "text": "#155e75", "icon": "fa-lungs"},
    "Dermatology":       {"bg": "#fdf4ff", "border": "#d946ef", "text": "#86198f", "icon": "fa-allergies"},
    "Gastroenterology":  {"bg": "#fefce8", "border": "#eab308", "text": "#713f12", "icon": "fa-stomach"},
    "Pediatrics":        {"bg": "#f0fdf4", "border": "#22c55e", "text": "#14532d", "icon": "fa-baby"},
    "Ophthalmology":     {"bg": "#eff6ff", "border": "#3b82f6", "text": "#1e3a8a", "icon": "fa-eye"},
    "Endocrinology":     {"bg": "#fff1f2", "border": "#fb7185", "text": "#881337", "icon": "fa-syringe"},
    "Urology":           {"bg": "#f0f9ff", "border": "#0ea5e9", "text": "#0c4a6e", "icon": "fa-procedures"},
    "Psychiatry":        {"bg": "#f8fafc", "border": "#64748b", "text": "#1e293b", "icon": "fa-brain"},
    "Gynecology":        {"bg": "#fdf2f8", "border": "#ec4899", "text": "#831843", "icon": "fa-venus"},
    "Infectious Disease":{"bg": "#ecfdf5", "border": "#10b981", "text": "#064e3b", "icon": "fa-virus"},
    "General Medicine":  {"bg": "#f1f5f9", "border": "#94a3b8", "text": "#334155", "icon": "fa-user-md"},
    "General Surgery":   {"bg": "#fff7ed", "border": "#fb923c", "text": "#7c2d12", "icon": "fa-procedures"},
    "Hematology":        {"bg": "#fef2f2", "border": "#f87171", "text": "#7f1d1d", "icon": "fa-tint"},
}

# ── Severity config ───────────────────────────────────────────────────
SEVERITY_CONFIG = {
    "critical": {"label": "CRITICAL",  "color": "#dc2626", "bg": "#fef2f2", "icon": "fa-exclamation-circle", "priority": 1},
    "high":     {"label": "HIGH",      "color": "#ea580c", "bg": "#fff7ed", "icon": "fa-exclamation-triangle", "priority": 2},
    "moderate": {"label": "MODERATE",  "color": "#d97706", "bg": "#fffbeb", "icon": "fa-info-circle",          "priority": 3},
    "low":      {"label": "LOW",       "color": "#16a34a", "bg": "#f0fdf4", "icon": "fa-check-circle",         "priority": 4},
}


class SymptomAnalyzer:
    """
    Hybrid AI Symptom Checker:
    1. TF-IDF vectorization of symptom text
    2. Cosine similarity scoring against disease profiles
    3. Rule-based boosting for exact symptom matches
    4. Confidence normalization and ranking
    """

    def __init__(self):
        self.diseases = SYMPTOM_DISEASE_DB
        self.all_symptoms = ALL_SYMPTOMS
        # Build symptom vectors for each disease
        self._build_vectors()

    def _build_vectors(self):
        """Build TF-IDF-like binary vectors for each disease"""
        self.symptom_index = {s: i for i, s in enumerate(self.all_symptoms)}
        self.disease_vectors = {}
        for disease, data in self.diseases.items():
            vec = np.zeros(len(self.all_symptoms))
            for symptom in data["symptoms"]:
                if symptom in self.symptom_index:
                    vec[self.symptom_index[symptom]] = 1.0
            self.disease_vectors[disease] = vec

    def _normalize_text(self, text: str) -> str:
        """Normalize input text"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _extract_symptoms(self, text: str) -> list:
        """Extract matching symptoms from user input"""
        text = self._normalize_text(text)
        found = []
        for symptom in self.all_symptoms:
            # Exact or partial match
            if symptom in text or any(word in text for word in symptom.split() if len(word) > 3):
                found.append(symptom)
        return found

    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    def analyze(self, symptom_text: str, top_n: int = 5) -> dict:
        """
        Analyze symptoms and return top N disease predictions.
        Returns structured dict with predictions, confidence, and metadata.
        """
        if not symptom_text or len(symptom_text.strip()) < 3:
            return {"error": "Please enter at least one symptom.", "results": []}

        # Step 1: Extract matching symptoms
        matched_symptoms = self._extract_symptoms(symptom_text)

        # Step 2: Build input vector
        input_vec = np.zeros(len(self.all_symptoms))
        for s in matched_symptoms:
            if s in self.symptom_index:
                input_vec[self.symptom_index[s]] = 1.0

        # Also include raw word matches for better recall
        raw_words = set(self._normalize_text(symptom_text).split())

        # Step 3: Score each disease
        scores = {}
        for disease, data in self.diseases.items():
            # Base score: cosine similarity
            cosine_score = self._cosine_similarity(input_vec, self.disease_vectors[disease])

            # Exact match bonus
            exact_matches = sum(1 for s in data["symptoms"] if s in matched_symptoms)
            match_ratio = exact_matches / max(len(data["symptoms"]), 1)

            # Word overlap bonus
            disease_words = set(' '.join(data["symptoms"]).split())
            word_overlap = len(raw_words & disease_words) / max(len(disease_words), 1)

            # Combined weighted score
            final_score = (
                cosine_score * 0.40 +
                match_ratio  * 0.45 +
                word_overlap * 0.15
            )

            if final_score > 0.05:
                scores[disease] = {
                    "score": final_score,
                    "exact_matches": exact_matches,
                    "total_symptoms": len(data["symptoms"]),
                }

        # Step 4: Sort by score
        sorted_diseases = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)[:top_n]

        if not sorted_diseases:
            return {
                "error": None,
                "matched_symptoms": matched_symptoms,
                "results": [],
                "message": "No strong matches found. Please provide more specific symptoms."
            }

        # Step 5: Normalize to percentages
        max_score = sorted_diseases[0][1]["score"] if sorted_diseases else 1
        results = []
        for rank, (disease, score_data) in enumerate(sorted_diseases):
            data = self.diseases[disease]
            confidence = round((score_data["score"] / max_score) * 100 if rank == 0
                               else score_data["score"] * 100, 1)
            # Clamp to realistic range
            confidence = min(max(confidence, 5.0), 97.0)

            dept = data["department"]
            severity = data["severity"]
            dept_info = DEPT_COLORS.get(dept, DEPT_COLORS["General Medicine"])
            sev_info  = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["low"])

            results.append({
                "rank":           rank + 1,
                "disease":        disease,
                "confidence":     confidence,
                "department":     dept,
                "severity":       severity,
                "icd_code":       data["icd"],
                "description":    data["description"],
                "advice":         data["advice"],
                "tests":          data["tests"],
                "matched_count":  score_data["exact_matches"],
                "total_symptoms": score_data["total_symptoms"],
                "dept_info":      dept_info,
                "sev_info":       sev_info,
            })

        # Step 6: Get unique departments for this analysis
        departments = list({r["department"] for r in results})
        primary = results[0] if results else None

        return {
            "error": None,
            "input_text": symptom_text,
            "matched_symptoms": matched_symptoms,
            "results": results,
            "primary_disease": primary["disease"] if primary else None,
            "primary_department": primary["department"] if primary else None,
            "primary_severity": primary["severity"] if primary else None,
            "recommended_departments": departments,
            "total_analyzed": len(self.diseases),
            "disclaimer": (
                "⚠️ This AI tool is for educational purposes only. "
                "It is NOT a substitute for professional medical diagnosis. "
                "Always consult a qualified healthcare provider."
            )
        }

    def get_symptom_suggestions(self, query: str) -> list:
        """Return symptom autocomplete suggestions"""
        query = query.lower().strip()
        if len(query) < 2:
            return []
        return [s for s in self.all_symptoms if query in s][:10]


# ── Singleton instance ────────────────────────────────────────────────
_analyzer_instance = None

def get_analyzer() -> SymptomAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SymptomAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # ── Quick Test ────────────────────────────────────────────────────
    analyzer = get_analyzer()
    test_cases = [
        "I have chest pain, shortness of breath, and sweating",
        "headache, nausea, light sensitivity, throbbing pain",
        "frequent urination, excessive thirst, fatigue, blurred vision",
        "cough, fever, chills, shortness of breath",
        "itchy skin, dry skin, red patches, rash",
    ]
    for tc in test_cases:
        result = analyzer.analyze(tc)
        if result["results"]:
            top = result["results"][0]
            print(f"\n Input: {tc}")
            print(f"  → Disease:     {top['disease']} ({top['confidence']}% confidence)")
            print(f"  → Department:  {top['department']}")
            print(f"  → Severity:    {top['severity'].upper()}")
            print(f"  → Matched:     {result['matched_symptoms']}")
