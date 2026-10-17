import time
import threading
import streamlit as st
import cv2
import pandas as pd

from attendance_agent.database import (
    init_db, students, add_student, start_session, end_session,
    record_attendance, record_metrics, get_sessions, attendance_for_session,
    metrics_for_session, update_attendance_status
)
from attendance_agent.config import CAMERA_INDEX, ENABLE_CLOUD_AI
from attendance_agent.vision import (
    enroll_from_camera, train_recognizer, load_recognizer, process_frame
)
from attendance_agent.analytics import summarize_metrics
from attendance_agent.suggestions import teaching_suggestions
from attendance_agent.export import attendance_csv, metrics_csv

st.set_page_config(
    page_title="ClassPulse | Attendance Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#172033; --muted:#68758b; --line:#e5eaf2; --blue:#4263eb; --cyan:#13b8a6; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: linear-gradient(180deg,#f7f9fe 0%,#f5f7fb 45%,#f8fafc 100%); color:var(--ink); }
.block-container { padding-top:1.8rem; padding-bottom:2.5rem; max-width:1450px; }
[data-testid="stSidebar"] { background: #111a2e; border-right:1px solid #202b43; }
[data-testid="stSidebar"] * { color:#e8eefb; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .45rem .65rem; border-radius:10px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#24314d; }
.brand { font-family:'Manrope',sans-serif; font-weight:800; letter-spacing:-.7px; font-size:1.35rem; color:white; }
.brand-sub { color:#aab8d2; font-size:.78rem; margin-top:-4px; }
.hero { background:linear-gradient(115deg,#172554 0%,#243c91 52%,#4263eb 100%); color:white; border-radius:22px; padding:28px 30px; margin:0 0 22px 0; box-shadow:0 14px 34px rgba(36,60,145,.17); }
.hero-kicker { font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:1.7px; color:#c9d7ff; }
.hero-title { font-family:'Manrope',sans-serif; font-size:2rem; line-height:1.2; font-weight:800; margin:.35rem 0 .55rem 0; }
.hero-copy { color:#e0e8ff; font-size:.98rem; max-width:780px; }
.section-title { font-family:'Manrope',sans-serif; font-size:1.15rem; font-weight:800; color:#172033; margin:.4rem 0 .2rem 0; }
.section-copy { color:#68758b; font-size:.9rem; margin-bottom:1rem; }
.metric-card { background:white; border:1px solid #e7ecf4; border-radius:17px; padding:17px 19px; box-shadow:0 5px 18px rgba(26,43,77,.035); min-height:108px; }
.metric-label { color:#718096; font-size:.82rem; font-weight:600; }
.metric-value { color:#172033; font-family:'Manrope',sans-serif; font-size:1.85rem; font-weight:800; margin-top:.25rem; }
.metric-note { color:#8a96a9; font-size:.76rem; margin-top:.1rem; }
.panel { background:white; border:1px solid #e7ecf4; border-radius:18px; padding:20px 22px; box-shadow:0 5px 18px rgba(26,43,77,.035); margin-bottom:14px; }
.pill { display:inline-block; background:#e6fbf5; color:#087f68; padding:5px 10px; border-radius:99px; font-size:.75rem; font-weight:700; }
.small-muted { color:#7b879a; font-size:.82rem; }
div.stButton > button, div.stDownloadButton > button, button[kind="primary"] { border-radius:11px; font-weight:700; min-height:2.7rem; }
div[data-testid="stFormSubmitButton"] button { border-radius:11px; font-weight:700; min-height:2.7rem; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] { border:1px solid #e7ecf4; border-radius:13px; overflow:hidden; }
hr { border-color:#e5eaf2; }
footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div style="font-size:2rem">🎓</div><div class="brand">ClassPulse</div><div class="brand-sub">CLASSROOM INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Roster & Enrollment", "Live Session", "Analytics & Reports", "Privacy & Settings"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown(f'<span class="pill">{"HYBRID AI" if ENABLE_CLOUD_AI else "LOCAL-FIRST MODE"}</span>', unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div><div class='small-muted'>Attendance is a reviewable suggestion. Engagement signals are approximate proxies, not grades.</div>", unsafe_allow_html=True)

def hero(kicker, title, copy):
    st.markdown(f"""<div class="hero"><div class="hero-kicker">{kicker}</div>
    <div class="hero-title">{title}</div><div class="hero-copy">{copy}</div></div>""", unsafe_allow_html=True)

def section(title, copy=None):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if copy:
        st.markdown(f'<div class="section-copy">{copy}</div>', unsafe_allow_html=True)

def metric_card(label, value, note):
    st.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>""", unsafe_allow_html=True)

# ---------- Pages ----------
if page == "Overview":
    roster, sessions = students(), get_sessions()
    hero("YOUR CLASSROOM, AT A GLANCE", "Welcome to ClassPulse", "A local-first workspace for attendance, session signals, and educator-support insights — with human review built in.")
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("ENROLLED STUDENTS", len(roster), "In your local roster")
    with c2: metric_card("SESSIONS RECORDED", len(sessions), "Saved on this device")
    with c3: metric_card("RECOGNITION MODEL", "Ready" if load_recognizer()[0] is not None else "Not trained", "Local LBPH model")
    with c4: metric_card("AI MODE", "Hybrid" if ENABLE_CLOUD_AI else "Local", "Cloud suggestions optional")
    st.write("")
    left,right = st.columns([1.35,1])
    with left:
        with st.container(border=True):
            section("Quick start", "Follow these steps to get your first session running.")
            st.markdown("**01 · Build your roster**  \nAdd student codes and display names.")
            st.markdown("**02 · Enroll and train**  \nCapture face samples with consent, then train the local model.")
            st.markdown("**03 · Run a session**  \nStart the webcam and review results in Analytics & Reports.")
            if st.button("Go to roster & enrollment", type="primary", use_container_width=True):
                st.session_state["nav_hint"] = "Roster & Enrollment"
                st.rerun()
    with right:
        with st.container(border=True):
            section("Privacy by design", "Processing stays on this computer by default.")
            st.markdown("🔒 **Local storage** — SQLite and model files stay in the project folder.")
            st.markdown("📷 **No raw video archive** — frames are processed in memory.")
            st.markdown("☁️ **Optional cloud AI** — off by default; only aggregate metrics are sent.")
            st.caption("Always provide a manual attendance option and review automated matches.")

elif page == "Roster & Enrollment":
    hero("PEOPLE MANAGEMENT", "Roster & enrollment", "Add students, capture face samples locally, and train the recognition model.")
    left,right = st.columns([.9,1.1], gap="large")
    with left:
        with st.container(border=True):
            section("Add a student", "Use an internal code rather than a government ID or other sensitive identifier.")
            with st.form("add_student_form", clear_on_submit=True):
                code = st.text_input("Student code", placeholder="e.g. DS-001")
                name = st.text_input("Display name", placeholder="e.g. Student One")
                submitted = st.form_submit_button("＋ Add student", type="primary", use_container_width=True)
                if submitted:
                    if not code.strip() or not name.strip():
                        st.error("Enter both a student code and display name.")
                    else:
                        try:
                            add_student(code, name)
                            st.success("Student added to the local roster.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not add student: {exc}")
    roster = students()
    with right:
        with st.container(border=True):
            section("Current roster", f"{len(roster)} student(s) registered on this device.")
            if roster:
                st.dataframe(pd.DataFrame(roster)[["student_code","name","created_at"]], use_container_width=True, hide_index=True)
            else:
                st.info("Your roster is empty. Add your first student to continue.")
    if roster:
        st.write("")
        with st.container(border=True):
            section("Face enrollment & model training", "Capture one consenting person at a time, in good lighting.")
            options = {f'{s["student_code"]} — {s["name"]} (ID {s["id"]})': s for s in roster}
            selected = options[st.selectbox("Select student", list(options))]
            st.warning("Face samples are biometric data. Obtain informed consent and protect/delete samples according to institutional policy.")
            e1,e2 = st.columns(2)
            with e1:
                if st.button("📷 Capture 25 samples", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Opening webcam enrollment window..."):
                            count = enroll_from_camera(selected["id"], samples=25, camera_index=CAMERA_INDEX)
                        st.success(f"Captured {count} sample(s).")
                    except Exception as exc:
                        st.error(str(exc))
            with e2:
                if st.button("🧠 Train local recognizer", use_container_width=True):
                    try:
                        with st.spinner("Training local LBPH model..."):
                            count = train_recognizer(roster)
                        st.success(f"Model trained on {count} face crop(s).")
                    except Exception as exc:
                        st.error(str(exc))

elif page == "Live Session":
    hero("SESSION CONTROL", "Live classroom session", "Start a short test session, watch detections, then review the attendance suggestions.")
    st.info("Tip: first test with one enrolled person, good front lighting, and the camera at eye level.")
    with st.container(border=True):
        with st.form("session_form"):
            title = st.text_input("Session title", value="Classroom Session")
            duration = st.select_slider("Test duration", options=[15,30,60,120], value=30, format_func=lambda x: f"{x} seconds")
            st.caption("The webcam opens only after you click Start. Frames are not saved to disk.")
            start = st.form_submit_button("▶ Start test session", type="primary", use_container_width=True)
    if start:
        roster = students()
        if not roster:
            st.error("Add at least one student first.")
        else:
            recognizer, label_map = load_recognizer()
            if recognizer is None:
                st.warning("No trained model found. This session can collect face-presence metrics but cannot identify students.")
            session_id = start_session(title)
            cap = cv2.VideoCapture(CAMERA_INDEX)
            if not cap.isOpened():
                end_session(session_id)
                st.error("Could not open webcam. Check Windows camera permission or CAMERA_INDEX in .env.")
            else:
                preview = st.empty()
                status = st.empty()
                progress = st.progress(0)
                stop_event = threading.Event()
                # This bounded MVP loop uses a keyboard stop in the OpenCV window; Streamlit controls cannot interrupt a blocking loop.
                seen_this_session = set()
                previous_gray = None
                start_time, last_log = time.time(), 0
                try:
                    while time.time() - start_time < duration and not stop_event.is_set():
                        ok, frame = cap.read()
                        if not ok:
                            status.error("Camera frame unavailable.")
                            break
                        annotated, face_count, recognized, _ = process_frame(frame, recognizer, label_map)
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        movement = 0.0
                        if previous_gray is not None:
                            movement = float(cv2.absdiff(cv2.resize(gray,(160,120)), cv2.resize(previous_gray,(160,120))).mean()/255.0)
                        previous_gray = gray
                        now = time.time()
                        if now - last_log >= 5:
                            for student_id, confidence in recognized:
                                record_attendance(session_id, student_id, confidence)
                                seen_this_session.add(student_id)
                            record_metrics(session_id, face_count, len(recognized), movement, None)
                            last_log = now
                        preview.image(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                        elapsed = min(1.0, (now-start_time)/duration)
                        progress.progress(elapsed)
                        status.write(f"**Faces detected:** {face_count}　 ·　 **Recognized this frame:** {len(recognized)}　 ·　 **Movement proxy:** {movement:.4f}")
                        time.sleep(.04)
                finally:
                    cap.release()
                    end_session(session_id)
                progress.progress(1.0)
                st.success(f"Session complete. {len(seen_this_session)} distinct student(s) recognized at least once. Review all matches before finalizing.")
                st.session_state["last_session_id"] = session_id
    st.write("")
    with st.container(border=True):
        section("Optional audio activity test", "Measures microphone amplitude for two seconds. It does not record or transcribe speech.")
        if st.button("🎙 Sample microphone activity"):
            try:
                from attendance_agent.audio import capture_rms
                value = capture_rms(seconds=2)
                st.metric("RMS amplitude", f"{value:.5f}")
            except Exception as exc:
                st.error(f"Audio sampling unavailable: {exc}")

elif page == "Analytics & Reports":
    hero("SESSION INSIGHTS", "Analytics & reports", "Review attendance suggestions, inspect session trends, and export records.")
    sessions = get_sessions()
    if not sessions:
        st.info("No sessions recorded yet. Start a test session first.")
    else:
        choices = {f'#{s["id"]} · {s["title"]} · {s["started_at"]}': s for s in sessions}
        session = choices[st.selectbox("Select session", list(choices))]
        sid = session["id"]
        attendance, metrics = attendance_for_session(sid), metrics_for_session(sid)
        c1,c2,c3 = st.columns(3)
        with c1: metric_card("ATTENDANCE SUGGESTIONS", len(attendance), "Require human review")
        with c2: metric_card("METRIC SAMPLES", len(metrics), "Recorded during session")
        with c3: metric_card("SESSION STATUS", "Ended" if session.get("ended_at") else "Recorded", "Local session record")
        st.write("")
        with st.container(border=True):
            section("Attendance review", "Change each status, then save your review.")
            if attendance:
                df = pd.DataFrame(attendance)
                edited = st.data_editor(
                    df[["id","student_code","name","first_seen","last_seen","confidence","status"]],
                    use_container_width=True, hide_index=True,
                    column_config={"status": st.column_config.SelectboxColumn("Status", options=["Review","Present","Absent","Excused"])},
                    disabled=["id","student_code","name","first_seen","last_seen","confidence"],
                )
                if st.button("Save attendance review", type="primary"):
                    for _, row in edited.iterrows():
                        update_attendance_status(int(row["id"]), str(row["status"]))
                    st.success("Attendance statuses saved.")
            else:
                st.info("No identities were recognized. Check enrollment, lighting, and model training.")
        summary = summarize_metrics(metrics)
        if metrics:
            left,right = st.columns(2)
            with left:
                with st.container(border=True):
                    section("Presence & recognition", "Average counts per sample.")
                    chart_df = pd.DataFrame(metrics).set_index("captured_at")[["faces_detected","recognized_count"]]
                    st.line_chart(chart_df)
            with right:
                with st.container(border=True):
                    section("Movement proxy", "Movement is not a reliable measure of attention.")
                    st.line_chart(pd.DataFrame(metrics).set_index("captured_at")[["movement_score"]])
        with st.container(border=True):
            section("Teaching suggestions", "Suggestions are supportive prompts, not judgments about individual learners.")
            result = teaching_suggestions(summary)
            st.caption(f"Suggestion source: {result['source']}")
            for item in result["suggestions"]:
                st.markdown(f"- {item}")
        d1,d2 = st.columns(2)
        d1.download_button("⬇ Download attendance CSV", attendance_csv(sid), file_name=f"attendance_session_{sid}.csv", mime="text/csv", use_container_width=True)
        d2.download_button("⬇ Download metrics CSV", metrics_csv(sid), file_name=f"metrics_session_{sid}.csv", mime="text/csv", use_container_width=True)

else:
    hero("TRUST & CONTROL", "Privacy & settings", "Understand what stays local, what may leave the device, and how to handle classroom data responsibly.")
    with st.container(border=True):
        section("Data handling")
        st.markdown("""
        - **Local by default:** roster, face samples, database, and model files are stored in the project folders.
        - **No raw video archive:** camera frames are processed in memory and not saved by this app.
        - **Cloud AI is optional:** disabled by default. When enabled, aggregate session metrics only are sent to the configured Gemini API; no names, IDs, images, or audio are sent by this module.
        - **Retention:** delete `data/face_samples/` and `data/attendance.db` when your approved retention period ends.
        - **Access:** this MVP has no user login. Run on a trusted computer; do not expose it publicly.
        """)
    with st.container(border=True):
        section("Configuration")
        st.code(f"CAMERA_INDEX={CAMERA_INDEX}\nENABLE_CLOUD_AI={'true' if ENABLE_CLOUD_AI else 'false'}", language="dotenv")
        st.caption("Cloud mode also requires GEMINI_API_KEY and a supported GEMINI_MODEL in your .env file.")
    st.warning("Recognition can be wrong. Provide manual attendance as an alternative and never use movement/audio proxies as proof of inattention.")
