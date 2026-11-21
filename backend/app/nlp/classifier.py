"""Passage-pair similarity classifier (explainable, scikit-learn).

Four human-readable features per pair of passages:
  embedding_cosine : cosine of the local sentence embeddings
  tfidf_cosine     : cosine of TF-IDF vectors of the two texts
  jaccard          : word-set overlap
  length_ratio     : shorter / longer word count

A LogisticRegression is trained ONLY from a real labelled CSV supplied by the
user (columns: text_a,text_b,label with label 1 = similar / 0 = not).  No
dataset ships with this project, so by default the classifier is UNTRAINED and
UNVALIDATED: the API returns the feature values only and no prediction.
Reported precision/recall/F1 are computed on a held-out split of the user's own
dataset and are not benchmark results (e.g. they are not STS-Benchmark scores).
"""
import csv
import json
import os
import re

import numpy as np

FEATURE_NAMES = ["embedding_cosine", "tfidf_cosine", "jaccard", "length_ratio"]
_TOKEN_RE = re.compile(r"[a-z0-9]+")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
MODEL_PATH = os.path.abspath(os.path.join(MODEL_DIR, "pair_classifier.joblib"))
META_PATH = os.path.abspath(os.path.join(MODEL_DIR, "pair_classifier.json"))


def _tfidf_cosine(a, b):
    from sklearn.feature_extraction.text import TfidfVectorizer
    try:
        m = TfidfVectorizer().fit_transform([a, b])
    except ValueError:                       # empty vocabulary
        return 0.0
    return float((m[0].multiply(m[1])).sum())   # rows are L2-normalised


def pair_features(a, b, embedder):
    ea, eb = embedder.encode([a, b])
    wa, wb = set(_TOKEN_RE.findall(a.lower())), set(_TOKEN_RE.findall(b.lower()))
    union = wa | wb
    la, lb = len(a.split()), len(b.split())
    return {
        "embedding_cosine": float(ea @ eb),
        "tfidf_cosine": _tfidf_cosine(a, b),
        "jaccard": len(wa & wb) / len(union) if union else 0.0,
        "length_ratio": (min(la, lb) / max(la, lb)) if max(la, lb) else 0.0,
    }


def _vector(feats):
    return [feats[n] for n in FEATURE_NAMES]


def train_from_csv(csv_path, embedder, min_rows=20):
    """Train + evaluate on a held-out 30% split. Raises ValueError if the data is unsuitable."""
    import joblib
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from app.nlp.metrics import precision_recall_f1

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append((r["text_a"], r["text_b"], int(r["label"])))
    labels = [r[2] for r in rows]
    if len(rows) < min_rows or len(set(labels)) < 2:
        raise ValueError(f"Need at least {min_rows} rows with both classes; got {len(rows)} rows.")

    X = np.array([_vector(pair_features(a, b, embedder)) for a, b, _ in rows])
    y = np.array(labels)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=1000).fit(Xtr, ytr)
    pred = model.predict(Xte)
    p, r, f1 = precision_recall_f1(yte.tolist(), pred.tolist())

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    meta = {"dataset": os.path.basename(csv_path), "rows": len(rows),
            "train_rows": int(len(ytr)), "test_rows": int(len(yte)),
            "embedding_backend": embedder.name, "features": FEATURE_NAMES,
            "coefficients": dict(zip(FEATURE_NAMES, map(float, model.coef_[0]))),
            "held_out": {"precision": p, "recall": r, "f1": f1},
            "note": "Held-out split of the supplied dataset only; not a benchmark result."}
    with open(META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return meta


def model_status():
    if os.path.exists(MODEL_PATH) and os.path.exists(META_PATH):
        with open(META_PATH, encoding="utf-8") as fh:
            return {"trained": True, **json.load(fh)}
    return {"trained": False,
            "note": ("No labelled dataset has been used: the classifier is untrained and "
                     "unvalidated. Only the feature values are reported.")}


def classify_pair(a, b, embedder):
    feats = pair_features(a, b, embedder)
    status = model_status()
    result = {"features": feats, "model": status, "prediction": None}
    if status["trained"] and status.get("embedding_backend") == embedder.name:
        import joblib
        model = joblib.load(MODEL_PATH)
        prob = float(model.predict_proba([_vector(feats)])[0][1])
        result["prediction"] = {"similar": prob >= 0.5, "probability": round(prob, 4)}
    elif status["trained"]:
        result["model"] = {**status, "note": "Model was trained with a different embedding backend; "
                                             "retrain before using it."}
    return result
