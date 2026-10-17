import pandas as pd
from .database import attendance_for_session, metrics_for_session

def attendance_csv(session_id):
    return pd.DataFrame(attendance_for_session(session_id)).to_csv(index=False).encode("utf-8")

def metrics_csv(session_id):
    return pd.DataFrame(metrics_for_session(session_id)).to_csv(index=False).encode("utf-8")
