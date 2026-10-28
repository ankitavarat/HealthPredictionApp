"""SQLite persistence layer."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "patients.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL,
    dob         TEXT NOT NULL,                     -- stored as ISO yyyy-mm-dd
    email       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    glucose     REAL NOT NULL,
    haemoglobin REAL NOT NULL,
    cholesterol REAL NOT NULL,
    remarks     TEXT NOT NULL DEFAULT ''
);
"""


def get_conn(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)


def create_patient(data: dict, remarks: str, db_path=DB_PATH) -> int:
    with get_conn(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO patients (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data["full_name"], data["dob"].isoformat(), data["email"],
             data["glucose"], data["haemoglobin"], data["cholesterol"], remarks),
        )
        return cur.lastrowid


def get_all_patients(db_path=DB_PATH):
    with get_conn(db_path) as conn:
        return conn.execute("SELECT * FROM patients ORDER BY id").fetchall()


def get_patient(patient_id: int, db_path=DB_PATH):
    with get_conn(db_path) as conn:
        return conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()


def email_exists(email: str, exclude_id=None, db_path=DB_PATH) -> bool:
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM patients WHERE email = ? AND id IS NOT ?", (email, exclude_id)
        ).fetchone()
        return row is not None


def update_patient(patient_id: int, data: dict, remarks: str, db_path=DB_PATH):
    with get_conn(db_path) as conn:
        conn.execute(
            "UPDATE patients SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?, "
            "cholesterol=?, remarks=? WHERE id=?",
            (data["full_name"], data["dob"].isoformat(), data["email"], data["glucose"],
             data["haemoglobin"], data["cholesterol"], remarks, patient_id),
        )


def update_remarks(patient_id: int, remarks: str, db_path=DB_PATH):
    with get_conn(db_path) as conn:
        conn.execute("UPDATE patients SET remarks=? WHERE id=?", (remarks, patient_id))


def delete_patient(patient_id: int, db_path=DB_PATH):
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
