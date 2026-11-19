"""
Puts the DEMO data back to a clean starting point before a presentation.

It resets:   leave requests, leave balances, demo passwords, chat history
It leaves:   orders, invoices, stock, suppliers, attendance, payslips and all accounts

Run from backend/ :    python reset_demo.py
(add --yes to skip the confirmation question)
"""

import subprocess
import sys

from app import create_app, db
from app.models.user import User
from app.models.employee import Employee, LeaveRequest
from app.models.chat_log import ChatLog

DEMO_BALANCES = {
    "Aditi Sharma": 14, "Rahul Verma": 20, "Priya Nair": 9, "Neha Kapoor": 16,
    "Vikram Singh": 12, "Meera Iyer": 15, "Arjun Mehta": 10,
}
DEMO_USERS = ["aditi", "rahul", "vikram", "admin"]

if "--yes" not in sys.argv:
    answer = input("This clears leave requests and chat history and resets demo balances. Type yes to continue: ")
    if answer.strip().lower() != "yes":
        print("Cancelled. Nothing was changed.")
        raise SystemExit

app = create_app()

with app.app_context():
    removed_requests = db.session.query(LeaveRequest).delete()
    removed_logs = db.session.query(ChatLog).delete()

    for name, balance in DEMO_BALANCES.items():
        emp = Employee.query.filter_by(name=name).first()
        if emp:
            emp.leave_balance = balance

    for username in DEMO_USERS:
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password("test123")

    db.session.commit()
    print(f"Removed {removed_requests} leave request(s) and {removed_logs} chat log(s).")
    print("Leave balances and demo passwords (test123) are back to normal.")

# Refill the analytics page with demo history
result = subprocess.run([sys.executable, "seed_chat_history.py"], capture_output=True, text=True)
print(result.stdout.strip().splitlines()[-1] if result.stdout.strip() else "Chat history seeding finished.")
print("Demo is ready.")