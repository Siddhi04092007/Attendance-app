import json
import cv2
import numpy as np
from .config import FACE_DIR, LBPH_PATH, LABELS_PATH

def _face_detector():
    xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(xml)
    if detector.empty():
        raise RuntimeError("OpenCV face detector could not be loaded.")
    return detector

def detect_faces(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = _face_detector().detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(70,70))
    return gray, faces

def enroll_from_camera(student_id, samples=25, camera_index=0):
    student_dir = FACE_DIR / str(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Check permissions or CAMERA_INDEX.")
    saved = 0
    try:
        while saved < samples:
            ok, frame = cap.read()
            if not ok:
                continue
            gray, faces = detect_faces(frame)
            if len(faces):
                x,y,w,h = max(faces, key=lambda b: b[2]*b[3])
                crop = cv2.resize(gray[y:y+h, x:x+w], (200,200))
                cv2.imwrite(str(student_dir / f"{saved:03d}.png"), crop)
                saved += 1
            cv2.imshow("Enrollment - look at camera, press q to stop", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return saved

def train_recognizer(student_records):
    if not hasattr(cv2, "face"):
        raise RuntimeError("LBPH requires opencv-contrib-python. Uninstall opencv-python if both are installed.")
    faces, labels = [], []
    label_to_student = {}
    label_num = 0
    for student in student_records:
        folder = FACE_DIR / str(student["id"])
        images = sorted(folder.glob("*.png")) if folder.exists() else []
        if not images:
            continue
        label_to_student[str(label_num)] = int(student["id"])
        for image_path in images:
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                faces.append(cv2.resize(image, (200,200)))
                labels.append(label_num)
        label_num += 1
    if not faces:
        raise RuntimeError("No enrolled face samples found. Enroll at least one student first.")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, np.array(labels, dtype=np.int32))
    recognizer.write(str(LBPH_PATH))
    LABELS_PATH.write_text(json.dumps(label_to_student, indent=2), encoding="utf-8")
    return len(faces)

def load_recognizer():
    if not hasattr(cv2, "face") or not LBPH_PATH.exists() or not LABELS_PATH.exists():
        return None, {}
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(LBPH_PATH))
    return recognizer, json.loads(LABELS_PATH.read_text(encoding="utf-8"))

def process_frame(frame, recognizer=None, label_map=None, threshold=75):
    gray, faces = detect_faces(frame)
    annotated = frame.copy()
    recognized = []
    for (x,y,w,h) in faces:
        crop = cv2.resize(gray[y:y+h, x:x+w], (200,200))
        name, confidence, student_id = "Unknown", None, None
        if recognizer is not None:
            label, distance = recognizer.predict(crop)
            confidence = float(distance)  # LBPH distance: lower is better, not a probability.
            if confidence <= threshold:
                student_id = label_map.get(str(label))
                if student_id is not None:
                    name = f"Student #{student_id}"
                    recognized.append((student_id, confidence))
        color = (40,180,40) if student_id is not None else (0,165,255)
        cv2.rectangle(annotated, (x,y), (x+w,y+h), color, 2)
        cv2.putText(annotated, name, (x, max(20,y-8)), cv2.FONT_HERSHEY_SIMPLEX, .55, color, 2)
    return annotated, len(faces), recognized, 0.0
