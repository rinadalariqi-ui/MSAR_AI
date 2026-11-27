import json
from pathlib import Path

import pandas as pd

LIST_COLUMNS = {"eligible_degrees", "eligible_majors", "required_documents"}

def _parse_list(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(str(value))
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except (json.JSONDecodeError, TypeError):
        return [item.strip() for item in str(value).split(",") if item.strip()]

def load_scholarships(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"لم يتم العثور على ملف المنح: {path}")
    frame = pd.read_csv(path, encoding="utf-8-sig")
    for column in LIST_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].apply(_parse_list)
    return frame.where(pd.notna(frame), None)
