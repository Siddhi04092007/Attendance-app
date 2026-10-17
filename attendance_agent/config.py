import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(ROOT / "data")))
MODEL_DIR = Path(os.getenv("MODEL_DIR", str(ROOT / "models")))
FACE_DIR = DATA_DIR / "face_samples"
DB_PATH = DATA_DIR / "attendance.db"
LBPH_PATH = MODEL_DIR / "lbph_model.yml"
LABELS_PATH = MODEL_DIR / "labels.json"
ENABLE_CLOUD_AI = os.getenv("ENABLE_CLOUD_AI", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

for path in (DATA_DIR, MODEL_DIR, FACE_DIR):
    path.mkdir(parents=True, exist_ok=True)
