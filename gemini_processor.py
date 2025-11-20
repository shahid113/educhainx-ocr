import os
import json
import google.generativeai as genai

# Load Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise Exception("Missing environment variable: GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT = """
Extract and map the following fields from the provided certificate text. 
Return VALID JSON ONLY — no explanation, no markdown, no comments, no extra text.

Required JSON structure:
{
  "certificateNo": "",
  "dateofIssue": "",
  "name": "",
  "enrolmentNo": "",
  "graduationYear": "",
  "degree": "",
  "department": ""
}

Extraction Rules:
- "certificateNo": Look for Certificate No, Serial No, Reg No, Roll No, or any unique identifier appearing at the top or header.
- "dateofIssue": May appear printed or handwritten. Normalize to YYYY-MM-DD. If multiple dates exist, choose the one closest to issuing authority or signature.
- "name": Student / recipient name, usually centered or emphasized.
- "enrolmentNo": Enrollment / Enrolment / Registration / Roll number unique to the student.
- "graduationYear": Year when the student completed or passed final exams.
- "degree": Degree awarded (e.g., Bachelor of Technology, B.Tech, BSc, etc.)
- "department": Field of study; may be shown as Department, Discipline, Branch, Programme, Subject, or Specialization.
- If any field is missing or unclear → "" (empty string).
- Do NOT infer values that do not explicitly appear in the text (no hallucinations).
- All values must be strings.
- Do NOT add extra keys.

OCR TEXT:
--------------------
{TEXT}
--------------------

Return ONLY the JSON object:
"""

# ---------------------------------------------------------
# CLEANING FUNCTION (Fixes all Gemini issues)
# ---------------------------------------------------------
def clean_gemini_output(raw: str) -> str:
    cleaned = raw.strip()

    # Remove code fences
    cleaned = cleaned.replace("```json", "")
    cleaned = cleaned.replace("```", "")

    # Remove stray backticks
    cleaned = cleaned.replace("`", "")

    return cleaned.strip()


# ---------------------------------------------------------
# MAIN PARSER
# ---------------------------------------------------------
def extract_certificate_json(text: str) -> dict:
    prompt = PROMPT.replace("{TEXT}", text)

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Clean formatting issues BEFORE json.loads
    cleaned = clean_gemini_output(raw)

    # Now safely parse JSON
    try:
        return json.loads(cleaned)
    except Exception:
        raise Exception("Gemini returned invalid JSON:\n" + raw)
