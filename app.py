"""Health Prediction Application - Flask backend."""
import os
import sqlite3
from datetime import date

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

import database as db
from ai_service import AIServiceError, predict_health_risk
from validators import validate_patient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-secret")

AI_PENDING = "AI prediction pending - use 'Re-run AI' to retry."


@app.template_filter("ddmmyyyy")
def ddmmyyyy(iso_text: str) -> str:
    return date.fromisoformat(iso_text).strftime("%d/%m/%Y")


def get_remarks(data: dict) -> tuple[str, str | None]:
    """Return (remarks, error_message). On AI failure the record is still saved."""
    try:
        return predict_health_risk(data), None
    except AIServiceError as exc:
        return AI_PENDING, str(exc)


def dup_email_error(email: str, exclude_id=None) -> dict:
    if db.email_exists(email, exclude_id):
        return {"email": "A patient with this email already exists."}
    return {}


# ---------- READ ----------
@app.route("/")
def index():
    return render_template("index.html", patients=db.get_all_patients())


# ---------- CREATE ----------
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("form.html", patient=None, values={}, errors={})

    data, errors = validate_patient(request.form)
    if "email" in data:
        errors.update(dup_email_error(data["email"]))
    if errors:
        return render_template("form.html", patient=None, values=request.form, errors=errors), 400

    remarks, ai_error = get_remarks(data)
    try:
        db.create_patient(data, remarks)
    except sqlite3.IntegrityError:
        errors["email"] = "A patient with this email already exists."
        return render_template("form.html", patient=None, values=request.form, errors=errors), 400

    flash(f"Record for {data['full_name']} created.", "success")
    if ai_error:
        flash(f"Saved, but AI prediction failed: {ai_error}", "warning")
    return redirect(url_for("index"))


# ---------- UPDATE ----------
@app.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit(patient_id):
    patient = db.get_patient(patient_id)
    if patient is None:
        flash("Record not found.", "danger")
        return redirect(url_for("index"))

    if request.method == "GET":
        values = {
            "full_name": patient["full_name"],
            "dob": date.fromisoformat(patient["dob"]).strftime("%d/%m/%Y"),
            "email": patient["email"],
            "glucose": patient["glucose"],
            "haemoglobin": patient["haemoglobin"],
            "cholesterol": patient["cholesterol"],
        }
        return render_template("form.html", patient=patient, values=values, errors={})

    data, errors = validate_patient(request.form)
    if "email" in data:
        errors.update(dup_email_error(data["email"], exclude_id=patient_id))
    if errors:
        return render_template("form.html", patient=patient, values=request.form, errors=errors), 400

    # Re-run the AI only when something that affects the prediction has changed.
    health_inputs_changed = (
        data["dob"].isoformat() != patient["dob"]
        or data["glucose"] != patient["glucose"]
        or data["haemoglobin"] != patient["haemoglobin"]
        or data["cholesterol"] != patient["cholesterol"]
    )
    remarks, ai_error = (patient["remarks"], None)
    if health_inputs_changed:
        remarks, ai_error = get_remarks(data)

    try:
        db.update_patient(patient_id, data, remarks)
    except sqlite3.IntegrityError:
        errors["email"] = "A patient with this email already exists."
        return render_template("form.html", patient=patient, values=request.form, errors=errors), 400

    flash("Record updated.", "success")
    if ai_error:
        flash(f"Saved, but AI prediction failed: {ai_error}", "warning")
    return redirect(url_for("index"))


# ---------- Re-run AI ----------
@app.route("/predict/<int:patient_id>", methods=["POST"])
def predict(patient_id):
    patient = db.get_patient(patient_id)
    if patient is None:
        flash("Record not found.", "danger")
        return redirect(url_for("index"))
    data = {
        "dob": date.fromisoformat(patient["dob"]),
        "glucose": patient["glucose"],
        "haemoglobin": patient["haemoglobin"],
        "cholesterol": patient["cholesterol"],
    }
    try:
        db.update_remarks(patient_id, predict_health_risk(data))
        flash("AI remarks updated.", "success")
    except AIServiceError as exc:
        flash(f"AI prediction failed: {exc}", "danger")
    return redirect(url_for("index"))


# ---------- DELETE ----------
@app.route("/delete/<int:patient_id>", methods=["POST"])
def delete(patient_id):
    patient = db.get_patient(patient_id)
    if patient is None:
        flash("Record not found.", "danger")
    else:
        db.delete_patient(patient_id)
        flash(f"Record for {patient['full_name']} deleted.", "success")
    return redirect(url_for("index"))


db.init_db()

if __name__ == "__main__":
    app.run(debug=True)
