# Health Prediction Application

A small CRUD application that stores patient blood-test results and uses an external AI API
(Google Gemini) to generate a possible health-risk remark for each patient.

**Stack:** Python 3, Flask, SQLite, Bootstrap 5, Google Gemini REST API.

## Features
- Create, read, update and delete patient records
- Server-side validation (name, dd/mm/yyyy date of birth, email format, numeric blood values, duplicate email)
- Persistent storage in SQLite (`patients.db`, created automatically)
- AI remarks generated on create, and on edit when DOB or blood values change
- If the AI API fails, the record is still saved and can be retried with **Re-run AI**

## Project structure
```
app.py            Flask routes (CRUD + AI trigger)
database.py       SQLite access layer
validators.py     Input validation rules
ai_service.py     Gemini API integration
templates/        Jinja2 + Bootstrap pages
.env     Template for configuration 
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Linux/macOS: cp .env.example .env
```
Edit `.env` and add your own Gemini API key (free from https://aistudio.google.com/apikey).

```bash
python app.py
```
Open http://127.0.0.1:5000

## Validation rules
| Field | Rule |
|---|---|
| Full name | 2-100 chars, letters, spaces, `. ' -` |
| Date of birth | Real calendar date, dd/mm/yyyy (dd.mm.yyyy and dd-mm-yyyy are normalised), not in the future, not older than 120 years |
| Email | Valid format, unique across records |
| Glucose | Number, 20-800 mg/dL |
| Haemoglobin | Number, 3-25 g/dL |
| Cholesterol | Number, 50-600 mg/dL |

## Expected results for the Task 2 test data
| # | Name | Result | Reason |
|---|---|---|---|
| 1 | Robyn Pears | Saved | Valid |
| 2 | John Hunter | Rejected | Email `hunter@gmail` has no domain extension |
| 3 | Darryl Tim | Saved | Valid (AI should flag high haemoglobin/cholesterol) |
| 4 | Peter Larry | Rejected | 31/11/2001 does not exist (November has 30 days) |
| 5 | Sam Kerr | Saved | Valid |
| 6 | Robyn Pears | Rejected | Duplicate email of record 1 |
| 7 | Madison XI | Saved | Valid |
| 8 | Kris Wu | Rejected | DOB 19/10/2030 is in the future; email `Kris.wu.gmail.com` has no `@` |
| 9 | Tenille Singh | Saved | Valid |
| 10 | Prem Kumar | Saved | Valid |

Note: in the task sheet, rows 8 and 9 run together ("1979 Tenille"); this is read as Kris Wu
cholesterol = 197 and test #9 = Tenille Singh.

## Disclaimer
AI remarks are informational only and are not a medical diagnosis.
