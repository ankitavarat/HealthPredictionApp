"""Calls the Google Gemini API to produce a health-risk remark from blood test values."""
import os
from datetime import date

import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 25


class AIServiceError(Exception):
    """Raised when the AI API cannot return a usable prediction."""


def _age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def build_prompt(data: dict) -> str:
    return (
        "You are a clinical decision-support assistant. Based on the blood test results below, "
        "state the most likely health condition or disease risk (for example diabetes, pre-diabetes, "
        "anaemia, polycythaemia, high cardiovascular risk, or 'no significant risk').\n"
        f"Age: {_age(data['dob'])} years\n"
        f"Fasting glucose: {data['glucose']} mg/dL\n"
        f"Haemoglobin: {data['haemoglobin']} g/dL\n"
        f"Total cholesterol: {data['cholesterol']} mg/dL\n\n"
        "Reply in plain text, maximum 40 words, in this format: "
        "'<Risk level: Low/Moderate/High> - <possible condition(s)> - <one short suggestion>'. "
        "No markdown."
    )


def predict_health_risk(data: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise AIServiceError("GEMINI_API_KEY is not configured.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

    try:
        response = requests.post(
            GEMINI_URL.format(model=model),
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": build_prompt(data)}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 200},
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.Timeout:
        raise AIServiceError("The AI service timed out.")
    except requests.HTTPError as exc:
      details = exc.response.text[:1000] if exc.response is not None else ""
      raise AIServiceError(
        f"AI service returned HTTP {exc.response.status_code}: {details}"
      )
    except requests.RequestException:
        raise AIServiceError("Could not reach the AI service.")
    except (KeyError, IndexError, ValueError):
        raise AIServiceError("The AI service returned an unexpected response.")

    if not text:
        raise AIServiceError("The AI service returned an empty response.")
    return text
