"""
Fills chat_logs with realistic DEMO conversations spread over the last 14 days,
so the Analytics page has something to show.

Only runs if there are fewer than 40 chat logs (it never touches real history twice).
Run from backend/ :   python seed_chat_history.py
"""

import random
from datetime import datetime, timedelta

from app import create_app, db
from app.models.user import User
from app.models.chat_log import ChatLog

app = create_app()
random.seed(7)

# (question, intent, weight) grouped by who would ask it
EMPLOYEE_QS = [
    ("check leave balance", "check_leave_balance", 10), ("show my payslip", "payslip", 7),
    ("apply leave on 20 dec", "apply_leave", 5), ("show my attendance", "my_attendance", 5),
    ("show my leave requests", "my_leave_requests", 4), ("what items are low on stock", "low_stock_alert", 3),
    ("how many chairs do we have", "check_inventory", 3), ("hello", "greeting", 3), ("help", "help", 2),
    ("total stock value", "inventory_value", 1),
]
HR_QS = [
    ("pending approvals", "pending_approvals", 7), ("approve request 3", "decide_leave", 4),
    ("list all employees", "employee_list", 4), ("check leave balance for employee 12", "check_leave_balance", 3),
    ("payslip for employee 2", "payslip", 2), ("show my attendance", "my_attendance", 2),
]
MANAGER_QS = [
    ("show open orders", "sales_orders", 8), ("overdue invoices", "overdue_invoices", 7),
    ("sales summary", "sales_summary", 6), ("who is our top customer", "top_customer", 4),
    ("pending purchase orders", "purchase_orders", 5), ("unpaid invoices", "unpaid_invoices", 4),
    ("orders from acme", "sales_orders", 3), ("status of invoice 3", "invoice_lookup", 3),
    ("what items are low on stock", "low_stock_alert", 3), ("pending approvals", "pending_approvals", 2),
]
UNKNOWN_QS = ["tell me a joke", "what is the weather today", "reset my password", "book a cab to the airport",
              "who won the match", "how do i change my email", "show me the org chart", "export everything to excel"]
BLOCKED = [("show overdue invoices", "overdue_invoices",
            "Your role (employee) doesn't have access to the Finance module. Ask a manager or admin."),
           ("check leave balance for employee 12", "check_leave_balance",
            "You can only view your own HR records. HR and admin accounts can look up other employees."),
           ("list all employees", "employee_list", "Only HR and admin accounts can list employees."),
           ("show open orders", "sales_orders",
            "Your role (hr) doesn't have access to the Sales module. Ask a manager or admin.")]


def pick(pool):
    return random.choices(pool, weights=[w for *_, w in pool])[0]


with app.app_context():
    if db.session.query(ChatLog).count() >= 40:
        print("chat_logs already has enough history, skipping.")
        raise SystemExit

    users = {u.username: u for u in User.query.all()}
    cast = [(users.get("aditi"), EMPLOYEE_QS, 0.50), (users.get("rahul"), HR_QS, 0.20),
            (users.get("vikram"), MANAGER_QS, 0.25), (users.get("admin"), MANAGER_QS, 0.05)]
    cast = [c for c in cast if c[0]]
    if not cast:
        print("Run create_demo_users.py first."); raise SystemExit

    now = datetime.utcnow()
    count = 0
    for day in range(13, -1, -1):
        weekday = (now - timedelta(days=day)).weekday()
        volume = random.randint(2, 5) if weekday >= 5 else random.randint(9, 16)
        if day == 0:
            volume = random.randint(6, 10)
        for _ in range(volume):
            user, pool, _w = random.choices(cast, weights=[c[2] for c in cast])[0]
            when = (now - timedelta(days=day)).replace(hour=random.randint(8, 18),
                                                       minute=random.randint(0, 59), second=random.randint(0, 59))
            if when > now:
                when = now - timedelta(minutes=random.randint(1, 90))
            roll = random.random()
            if roll < 0.08:
                q, intent, resp = random.choice(UNKNOWN_QS), "unknown", "I'm not sure I understood that. Type 'help' to see what I can do."
            elif roll < 0.12 and user.role in ("employee", "hr"):
                q, intent, resp = random.choice(BLOCKED)
            else:
                q, intent, _w2 = pick(pool)
                resp = "(demo data)"
            db.session.add(ChatLog(user_id=user.id, query=q, detected_intent=intent,
                                   response=resp, timestamp=when))
            count += 1
    db.session.commit()
    print(f"Added {count} demo chat logs across the last 14 days.")