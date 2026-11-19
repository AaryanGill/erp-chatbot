import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from app.nlp.training_data import TRAINING_DATA


def normalize(text: str) -> str:
    """Remove ids, SKUs and dates so the model learns the sentence pattern, not the values."""
    t = text.lower()
    t = re.sub(r"\bsku\s*#?[a-z0-9\-]+", "sku", t)
    t = re.sub(r"\b(inv|ord|po)[-\s]?\d+\b", r"\1", t)
    t = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", t)
    t = re.sub(r"\d+", " ", t)
    t = re.sub(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def build_model():
    texts, labels = [], []
    for intent, examples in TRAINING_DATA.items():
        for ex in examples:
            texts.append(normalize(ex))
            labels.append(intent)

    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2)),
        LogisticRegression(C=20, max_iter=2000),
    )
    model.fit(texts, labels)
    return model


_model = build_model()


def predict(query: str):
    """Returns (intent, confidence between 0 and 1)."""
    probs = _model.predict_proba([normalize(query)])[0]
    best = probs.argmax()
    return _model.classes_[best], float(probs[best])