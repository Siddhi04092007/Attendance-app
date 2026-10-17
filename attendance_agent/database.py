import sqlite3
from datetime import datetime, timezone
from .config import DB_PATH

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            confidence REAL,
            status TEXT NOT NULL DEFAULT 'Review',
            UNIQUE(session_id, student_id),
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            captured_at TEXT NOT NULL,
            faces_detected INTEGER NOT NULL,
            recognized_count INTEGER NOT NULL,
            movement_score REAL NOT NULL,
            audio_rms REAL,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        """)

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def add_student(student_code, name):
    with connect() as con:
        con.execute("INSERT INTO students(student_code,name,created_at) VALUES(?,?,?)",
                    (student_code.strip(), name.strip(), now_iso()))

def students():
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM students ORDER BY name")]

def start_session(title):
    with connect() as con:
        cur = con.execute("INSERT INTO sessions(title,started_at) VALUES(?,?)",
                          (title.strip(), now_iso()))
        return cur.lastrowid

def end_session(session_id):
    with connect() as con:
        con.execute("UPDATE sessions SET ended_at=? WHERE id=?", (now_iso(), session_id))

def record_attendance(session_id, student_id, confidence=None):
    stamp = now_iso()
    with connect() as con:
        con.execute("""
        INSERT INTO attendance(session_id,student_id,first_seen,last_seen,confidence,status)
        VALUES(?,?,?,?,?,'Review')
        ON CONFLICT(session_id,student_id) DO UPDATE SET
          last_seen=excluded.last_seen,
          confidence=MIN(COALESCE(attendance.confidence, 999), COALESCE(excluded.confidence,999))
        """, (session_id, student_id, stamp, stamp, confidence))

def record_metrics(session_id, faces, recognized, movement, audio_rms=None):
    with connect() as con:
        con.execute("""INSERT INTO metrics
        (session_id,captured_at,faces_detected,recognized_count,movement_score,audio_rms)
        VALUES(?,?,?,?,?,?)""",
        (session_id, now_iso(), int(faces), int(recognized), float(movement), audio_rms))

def get_sessions():
    with connect() as con:
        return [dict(r) for r in con.execute("SELECT * FROM sessions ORDER BY id DESC")]

def attendance_for_session(session_id):
    with connect() as con:
        return [dict(r) for r in con.execute("""
        SELECT a.id, s.student_code, s.name, a.first_seen, a.last_seen,
               a.confidence, a.status, a.student_id
        FROM attendance a JOIN students s ON s.id=a.student_id
        WHERE a.session_id=? ORDER BY s.name
        """, (session_id,))]

def metrics_for_session(session_id):
    with connect() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM metrics WHERE session_id=? ORDER BY id", (session_id,))]

def update_attendance_status(attendance_id, status):
    with connect() as con:
        con.execute("UPDATE attendance SET status=? WHERE id=?", (status, attendance_id))
