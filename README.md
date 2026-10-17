# Multimodal Attendance & Engagement Agent
Hybrid local-first classroom analytics MVP. Video processing, face recognition (OpenCV LBPH), session metrics, and SQLite storage run locally. Optional cloud teaching suggestions use Gemini only when explicitly enabled.

## Responsible use and limitations
- Obtain informed consent and follow institutional policy before collecting biometric data or recording audio/video.
- Face recognition can make mistakes. Treat attendance as a reviewable suggestion, not a final disciplinary record. Provide manual correction.
- Engagement metrics are rough behavioral proxies (face presence, movement/inactivity, audio energy), **not reliable measurements of attention, learning, or intent**. Do not grade students or make high-stakes decisions from them.
- Raw frames/audio are not saved by default. Face samples are stored locally; protect the data folder and delete samples when no longer needed.
- Cloud calls are off by default. If enabled, only aggregate metrics are sent; never send images, audio, names, or student IDs.

## Requirements
Python 3.10 or 3.11 recommended. Webcam required for live capture. Install `opencv-contrib-python` for LBPH; do not install `opencv-python` alongside it.

## Setup (Windows PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope Process Bypass`

## First run
1. Open **Roster & Enrollment**, add a student name and local ID.
2. Enroll the student in good lighting. Capture starts only after you press the enrollment button.
3. Train the local recognizer.
4. Open **Live Session** and start camera processing.
5. Review attendance in **Reports** and export CSV.

## Optional hybrid AI
Set `ENABLE_CLOUD_AI=true` and `GEMINI_API_KEY` in `.env`. Set `GEMINI_MODEL` to a model available to your account. Only anonymous aggregate counts/percentages are sent; the provider may process that aggregate data under its terms. Keep cloud mode disabled if your institution requires fully offline processing.

## Project structure
```text
multimodal_attendance_agent/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── data/                  # created at runtime; keep private
├── models/                # generated local model files
└── attendance_agent/
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── vision.py
    ├── audio.py
    ├── analytics.py
    ├── suggestions.py
    └── export.py
```

## MVP boundaries
- LBPH is sensitive to lighting and camera angle and is not anti-spoofing.
- This starter measures movement and face presence, not validated head pose.
- Audio activity measures amplitude only; it does not identify speakers or transcribe speech.
- No login is included. Do not expose the Streamlit server to public networks without authentication, HTTPS, and a security review.
