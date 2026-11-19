"""
Usage analytics built from the chat_logs table.
Only managers and admins may see it.
"""

from datetime import datetime, timedelta, time

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, or_

from app import db
from app.models.user import User
from app.models.chat_log import ChatLog
from app.handlers import ROUTES, MODULE_LABELS

analytics_bp = Blueprint("analytics", __name__)

INTENT_LABELS = {
    "check_leave_balance": "Leave balance", "apply_leave": "Apply for leave",
    "my_leave_requests": "Leave requests", "employee_info": "Employee info",
    "employee_list": "Employee list", "my_attendance": "Attendance", "payslip": "Payslip",
    "check_inventory": "Stock lookup", "low_stock_alert": "Low stock",
    "inventory_value": "Stock value", "sales_orders": "Orders",
    "sales_summary": "Sales summary", "top_customer": "Top customer",
    "overdue_invoices": "Overdue invoices", "unpaid_invoices": "Unpaid invoices",
    "invoice_lookup": "Invoice lookup", "purchase_orders": "Purchase orders",
    "pending_approvals": "Pending approvals", "decide_leave": "Approve / reject",
    "greeting": "Greetings", "help": "Help", "dialogue": "Follow-up answers",
    "unknown": "Not understood", "error": "Errors",
}

# Replies that mean "the role was not allowed to do this"
BLOCKED_PATTERNS = ["Your role (%", "Only HR%", "You can only view%", "You can't approve%"]


def _module_of(intent):
    if intent in ROUTES:
        return MODULE_LABELS[ROUTES[intent][0]]
    if intent == "dialogue":
        return MODULE_LABELS["hr"]
    return "General"


@analytics_bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    user = User.query.get(int(get_jwt_identity()))
    if user.role not in ("manager", "admin"):
        return jsonify({"error": "Analytics is available to managers and admins."}), 403

    now = datetime.utcnow()
    today = now.date()

    total = db.session.query(ChatLog).count()
    today_count = db.session.query(ChatLog).filter(ChatLog.timestamp >= datetime.combine(today, time.min)).count()
    active_users = db.session.query(func.count(func.distinct(ChatLog.user_id))).scalar() or 0

    # ---- by intent
    rows = (db.session.query(ChatLog.detected_intent, func.count())
            .group_by(ChatLog.detected_intent).all())
    by_intent = {(i or "unknown"): n for i, n in rows}

    not_understood = by_intent.get("unknown", 0) + by_intent.get("error", 0)
    answered_pct = round(100 * (total - not_understood) / total, 1) if total else 0.0

    top_intents = sorted(
        ({"label": INTENT_LABELS.get(i, i), "count": n} for i, n in by_intent.items()
         if i not in ("unknown", "error")),
        key=lambda d: d["count"], reverse=True)[:8]

    by_module = {}
    for intent, n in by_intent.items():
        label = _module_of(intent)
        by_module[label] = by_module.get(label, 0) + n
    modules = sorted(({"label": k, "count": v} for k, v in by_module.items()),
                     key=lambda d: d["count"], reverse=True)

    # ---- questions per day (last 14 days, empty days filled with 0)
    start = today - timedelta(days=13)
    day_rows = (db.session.query(func.date(ChatLog.timestamp), func.count())
                .filter(ChatLog.timestamp >= datetime.combine(start, time.min))
                .group_by(func.date(ChatLog.timestamp)).all())
    day_counts = {str(d): n for d, n in day_rows}
    per_day = []
    for k in range(14):
        d = start + timedelta(days=k)
        per_day.append({"date": d.isoformat(), "label": d.strftime("%d %b"),
                        "count": day_counts.get(d.isoformat(), 0)})

    # ---- questions the bot did not understand (useful for retraining)
    unknown_rows = (db.session.query(ChatLog).filter(ChatLog.detected_intent.in_(["unknown", "error"]))
                    .order_by(ChatLog.timestamp.desc()).limit(40).all())
    seen, unanswered = set(), []
    for r in unknown_rows:
        key = r.query.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        unanswered.append({"query": r.query, "time": r.timestamp.strftime("%d %b, %H:%M")})
        if len(unanswered) == 6:
            break

    # ---- blocked by access control
    blocked = db.session.query(ChatLog).filter(or_(*[ChatLog.response.like(p) for p in BLOCKED_PATTERNS])).count()

    # ---- recent activity
    recent_rows = db.session.query(ChatLog).order_by(ChatLog.timestamp.desc()).limit(8).all()
    names = {u.id: u.username for u in User.query.filter(
        User.id.in_([r.user_id for r in recent_rows if r.user_id])).all()}
    recent = [{"user": names.get(r.user_id, "-"), "query": r.query,
               "topic": INTENT_LABELS.get(r.detected_intent, r.detected_intent or "-"),
               "time": r.timestamp.strftime("%d %b, %H:%M")} for r in recent_rows]

    return jsonify({
        "totals": {"questions": total, "today": today_count, "active_users": active_users,
                   "answered_pct": answered_pct, "blocked": blocked},
        "per_day": per_day, "top_intents": top_intents, "modules": modules,
        "unanswered": unanswered, "recent": recent,
    })