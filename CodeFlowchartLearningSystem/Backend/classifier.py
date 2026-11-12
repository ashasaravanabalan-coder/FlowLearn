"""Loads the trained Decision Tree and classifies code logic."""
import sys
from pathlib import Path
import joblib
import pandas as pd

ML_DIR = Path(__file__).resolve().parent.parent / "ML"
sys.path.insert(0, str(ML_DIR))
from features import extract_features  # noqa: E402

_bundle = None


def classify(code: str) -> dict:
    global _bundle
    if _bundle is None:
        _bundle = joblib.load(ML_DIR / "model.joblib")
    feats = extract_features(code)
    X = pd.DataFrame([feats])[_bundle["features"]]
    clf = _bundle["model"]
    proba = clf.predict_proba(X)[0]
    return {"logic_type": str(clf.predict(X)[0]), "confidence": round(float(proba.max()), 3), "features": feats}
