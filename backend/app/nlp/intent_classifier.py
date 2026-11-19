"""
Hybrid intent classifier for the ERP chatbot.

Three stages (first one that succeeds wins):
  1. Priority patterns : very specific phrases that always map to one intent.
  2. ML model          : TF-IDF + Logistic Regression trained on example sentences.
                         Used only when its confidence >= ML_THRESHOLD.
  3. Keyword scoring   : rule-based fallback for low-confidence queries.
"""

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from app.nlp.ml_classifier import predict as ml_predict

for pkg in ["punkt", "punkt_tab", "wordnet", "omw-1.4"]:
    nltk.download(pkg, quiet=True)

lemmatizer = WordNetLemmatizer()

ML_THRESHOLD = 0.40

PRIORITY_PATTERNS = [
    # A command: starts with the verb ("approve request 3") or has a number after it
    ("decide_leave", re.compile(
        r"^\s*(?:please\s+|pls\s+|kindly\s+|can you\s+|could you\s+)?(?:approve|reject|decline|deny)\b"
        r"|\b(?:approve|reject|decline|deny)\w*\b[^\d]*\d", re.I)),
    ("pending_approvals", re.compile(
        r"\bpending\s+approvals?\b|\bawaiting\b|\bwaiting\s+for\s+(?:my\s+)?approval\b"
        r"|\bto\s+approve\b|\bneeds?\s+(?:my\s+)?approval\b|\bfor\s+approval\b"
        r"|\bwho\s+(?:has\s+|have\s+)?applied\b"
        r"|^(?!.*\bmy\b).*\bpending\s+leave\s+requests?\b", re.I)),
    ("my_leave_requests",
     re.compile(r"\bleave\s+(requests?|status|history)\b|\bpending\s+leaves?\b|\bmy\s+requests?\b", re.I)),
    ("purchase_orders", re.compile(r"\bpurchase\s+orders?\b|\bpo[-\s]?#?\d+\b", re.I)),
    ("overdue_invoices", re.compile(r"\boverdue\b|\bpast\s+due\b|\blate\s+payments?\b", re.I)),
    ("invoice_lookup", re.compile(r"\binvoices?\s*(?:no\.?|number|id)?\s*#?\d+\b|\binv[-\s]?\d+\b", re.I)),
    ("payslip", re.compile(r"\bpay\s?slips?\b|\bsalary\s+slip\b", re.I)),
]

INTENTS = {
    "check_leave_balance": ["balance", "remaining", "pto"],
    "apply_leave": ["apply", "request", "book", "leave", "vacation"],
    "low_stock_alert": ["reorder", "low", "shortage", "restock"],
    "check_inventory": ["stock", "inventory", "quantity", "available"],
    "employee_info": ["employee", "profile", "designation", "department"],
    "employee_list": ["employees", "staff", "headcount"],
    "my_attendance": ["attendance", "present", "absent"],
    "payslip": ["payslip", "salary", "payroll"],
    "sales_orders": ["order", "orders"],
    "sales_summary": ["sales", "revenue"],
    "top_customer": ["customer", "client"],
    "unpaid_invoices": ["unpaid", "outstanding", "receivable"],
    "invoice_lookup": ["invoice"],
    "purchase_orders": ["supplier", "delivery", "purchase"],
    "inventory_value": ["worth", "valuation"],
    "pending_approvals": ["approval", "approvals"],
    "decide_leave": ["approve", "reject"],
    "greeting": ["hello", "hi", "hey", "morning"],
    "help": ["help", "command", "option"],
}

# Each entity can have several patterns; the first one that matches wins.
ENTITY_PATTERNS = {
    "employee_id": [r"\bemp(?:loyee)?\s*(?:id)?\s*#?(\d+)\b"],
    "item_sku": [r"\bsku\s*#?([A-Za-z0-9\-]+)\b"],
    "order_id": [r"(?<!purchase )\borders?\s*(?:no\.?|number|id)?\s*#?0*(\d+)\b",
                 r"\bord[-\s]?0*(\d+)\b"],
    "invoice_id": [r"\binvoices?\s*(?:no\.?|number|id)?\s*#?0*(\d+)\b",
                   r"\binv[-\s]?0*(\d+)\b"],
    "request_id": [r"\b(?:approve|reject|decline|deny)\w*\s+(?:the\s+)?(?:leave\s+)?(?:request\s+)?(?:no\.?|number|id)?\s*#?0*(\d+)\b",
                   r"\brequest\s*(?:no\.?|number|id)?\s*#?0*(\d+)\b"],
    "po_id": [r"\b(?:purchase\s+orders?|po)\s*(?:no\.?|number|id)?\s*#?0*(\d+)\b",
              r"\bpo[-\s]?0*(\d+)\b"],
}


def preprocess(text: str):
    tokens = word_tokenize(text.lower())
    return [lemmatizer.lemmatize(t) for t in tokens if t.isalnum()]


def keyword_classify(query: str):
    token_set = set(preprocess(query))
    scores = {}
    for intent, keywords in INTENTS.items():
        kw = {lemmatizer.lemmatize(k) for k in keywords}
        overlap = token_set & kw
        if overlap:
            scores[intent] = len(overlap) / len(kw)
    if not scores:
        return "unknown", 0.0
    best = max(scores, key=scores.get)
    return best, round(scores[best], 2)


def classify_intent(query: str):
    """Returns: {"intent", "confidence", "entities", "method"}"""
    entities = extract_entities(query)

    for intent_name, pattern in PRIORITY_PATTERNS:
        if pattern.search(query):
            return {"intent": intent_name, "confidence": 1.0, "entities": entities, "method": "pattern"}

    ml_intent, ml_conf = ml_predict(query)
    if ml_conf >= ML_THRESHOLD:
        return {"intent": ml_intent, "confidence": round(ml_conf, 2), "entities": entities, "method": "ml"}

    kw_intent, kw_conf = keyword_classify(query)
    return {"intent": kw_intent, "confidence": kw_conf, "entities": entities, "method": "keyword"}


def extract_entities(query: str):
    entities = {}
    for name, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities[name] = match.group(1)
                break
    return entities