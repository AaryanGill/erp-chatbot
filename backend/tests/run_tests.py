"""
Automated end-to-end tests for the ERP chatbot.

They run against a TEMPORARY SQLite database, so your real PostgreSQL data is
never touched. The database is built with the same seed scripts you use.

Run from backend/ :    python tests/run_tests.py
"""

import os
import subprocess
import sys
import tempfile
import warnings
from datetime import date, timedelta

warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tmp_dir = tempfile.mkdtemp()
db_file = os.path.join(tmp_dir, "test.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
os.environ["JWT_SECRET_KEY"] = "test-secret"
sys.path.insert(0, BACKEND)

# ---- build the test database with the project's own seed scripts
for script in ["seed.py", "seed_more.py", "create_demo_users.py", "seed_chat_history.py"]:
    result = subprocess.run([sys.executable, script], cwd=BACKEND, env=os.environ,
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Could not run {script}:\n{result.stderr[-800:]}")
        sys.exit(1)

from app import create_app                       # noqa: E402
from app.nlp.intent_classifier import classify_intent   # noqa: E402

app = create_app()
client = app.test_client()

passed, failed = 0, []


def check(name, condition, detail=""):
    global passed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed.append(name)
        print(f"  FAIL  {name}   {detail}")


def login(username, password="test123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    return {"Authorization": "Bearer " + r.get_json()["token"]}


def ask(headers, text):
    return client.post("/api/chat/message", json={"message": text}, headers=headers).get_json()


def section(title):
    print(f"\n{title}")


aditi, rahul, vikram, admin = login("aditi"), login("rahul"), login("vikram"), login("admin")
start = (date.today() + timedelta(days=10)).strftime("%d %b")
end = (date.today() + timedelta(days=12)).strftime("%d %b")

# ------------------------------------------------------------------ auth
section("Authentication")
check("wrong password is rejected",
      client.post("/api/auth/login", json={"username": "aditi", "password": "nope"}).status_code == 401)
check("chat without a token is rejected",
      client.post("/api/chat/message", json={"message": "hello"}).status_code == 401)
new = client.post("/api/auth/register", json={"username": "newbie", "email": "n@example.com",
                                              "password": "pw12345", "role": "admin"}).get_json()
check("registration ignores a requested admin role", new["user"]["role"] == "employee")
nb = {"Authorization": "Bearer " + new["token"]}
check("new account gets an employee record (18 days)", "18 leave day" in ask(nb, "check leave balance")["summary"])

# ------------------------------------------------------------------ NLP
section("Language understanding")
for text, intent in [("check leave balance", "check_leave_balance"), ("show my payslip", "payslip"),
                     ("approve request 3", "decide_leave"), ("which invoices are overdue", "overdue_invoices"),
                     ("can i get monday off", "apply_leave"), ("tell me a joke", "unknown"),
                     ("status of po 2", "purchase_orders"), ("how many chairs do we have", "check_inventory")]:
    got = classify_intent(text)["intent"]
    check(f"'{text}' -> {intent}", got == intent, f"got {got}")

# ------------------------------------------------------------------ employee
section("Employee (aditi)")
r = ask(aditi, "check leave balance")
check("sees own leave balance", "Aditi Sharma has 14" in r["summary"], r["summary"])
check("payslip returns a table", ask(aditi, "show my payslip")["table"] is not None)
check("attendance returns a table", ask(aditi, "show my attendance")["table"] is not None)
check("low stock list works", ask(aditi, "what items are low on stock")["table"] is not None)
for text in ["show overdue invoices", "show open orders", "pending purchase orders", "list all employees",
             "check leave balance for employee 12", "pending approvals", "approve request 1"]:
    check(f"blocked: '{text}'", ask(aditi, text)["module"] == "security")

# ------------------------------------------------------------------ leave flow
section("Leave application with confirmation")
r = ask(aditi, "apply leave")
check("asks for dates", r["summary"].startswith("Which dates"), r["summary"])
r = ask(aditi, f"from {start} to {end}")
check("asks for confirmation", "Reply 'yes' to confirm" in r["summary"], r["summary"])
r = ask(aditi, "yes")
check("request is saved", "submitted" in r["summary"], r["summary"])
check("balance dropped by 3", "Aditi Sharma has 11" in ask(aditi, "check leave balance")["summary"])
check("request is listed", ask(aditi, "show my leave requests")["table"]["rows"][0][-1] == "Pending")

ask(aditi, "apply leave tomorrow")
check("'no' cancels", "cancelled" in ask(aditi, "no")["summary"])
check("a later 'yes' does nothing", "submitted" not in ask(aditi, "yes")["summary"])

ask(aditi, "apply leave")
r = ask(aditi, "show my payslip")
check("changing topic drops the open question", r["table"] is not None)

ask(aditi, "apply leave tomorrow")
client.post("/api/auth/login", json={"username": "aditi", "password": "test123"})   # logging in clears memory
check("login clears an unanswered confirmation", "submitted" not in ask(aditi, "yes")["summary"])

# ------------------------------------------------------------------ approvals
section("Approvals (rahul = hr)")
r = ask(rahul, "pending approvals")
rows = r["table"]["rows"] if r["table"] else []
check("hr sees the pending request", any("Aditi" in row[1] for row in rows), str(rows))
req_id = next((row[0].lstrip("#") for row in rows if "Aditi" in row[1]), "0")
check("approve works", "approved" in ask(rahul, f"approve request {req_id}")["summary"])
check("deciding twice is refused", "already approved" in ask(rahul, f"approve request {req_id}")["summary"])

ask(aditi, "apply leave on " + (date.today() + timedelta(days=20)).strftime("%d %b"))
ask(aditi, "yes")
rows = ask(rahul, "pending approvals")["table"]["rows"]
rej_id = rows[0][0].lstrip("#")
before = ask(aditi, "check leave balance")["summary"]
check("reject works", "rejected" in ask(rahul, f"reject request {rej_id}")["summary"])
after = ask(aditi, "check leave balance")["summary"]
check("rejection returns the days", before != after, f"{before} / {after}")

ask(rahul, "apply leave on " + (date.today() + timedelta(days=25)).strftime("%d %b"))
ask(rahul, "yes")
own_id = ask(rahul, "pending approvals")["table"]["rows"][0][0].lstrip("#")
check("hr cannot approve own request", ask(rahul, f"approve request {own_id}")["module"] == "security")
check("a manager can approve it", "approved" in ask(vikram, f"approve request {own_id}")["summary"])
check("hr can list all employees", ask(rahul, "list all employees")["table"] is not None)
check("hr can read another employee", "Priya Nair" in ask(rahul, "check leave balance for employee 12")["summary"])
check("hr blocked from sales", ask(rahul, "show open orders")["module"] == "security")

# ------------------------------------------------------------------ manager business modules
section("Manager (vikram)")
r = ask(vikram, "show overdue invoices")
check("2 overdue invoices", r["table"] is not None and len(r["table"]["rows"]) == 2, r["summary"])
check("open orders table", ask(vikram, "show open orders")["table"] is not None)
check("orders from a named customer", "Acme" in ask(vikram, "orders from acme")["summary"])
check("status of one order", "ORD-0003" in ask(vikram, "status of order 3")["summary"])
check("top customer", "Stark" in ask(vikram, "who is our top customer")["summary"])
check("sales summary", "last 30 days" in ask(vikram, "sales summary")["summary"])
check("unpaid invoices", "outstanding" in ask(vikram, "unpaid invoices")["summary"])
check("invoice by number", "INV-0003" in ask(vikram, "status of invoice 3")["summary"])
check("purchase orders pending", ask(vikram, "pending purchase orders")["table"] is not None)
check("delivery by item name", "USB-C Hub" in ask(vikram, "when will the usb-c hub arrive")["summary"])
check("stock value", "Total stock value" in ask(vikram, "total stock value")["summary"])

section("Follow-up questions")
ask(vikram, "show invoices for globex")
check("'what about acme' keeps the topic", "Acme" in ask(vikram, "what about acme")["summary"])
ask(vikram, "status of order 3")
check("'and order 4'", "ORD-0004" in ask(vikram, "and order 4")["summary"])
ask(rahul, "check leave balance for employee 12")
check("follow-up for another employee", "Rahul Verma" in ask(rahul, "what about employee 2")["summary"])
ask(aditi, "check leave balance")
check("follow-up still respects access", ask(aditi, "what about employee 2")["module"] == "security")

# ------------------------------------------------------------------ dashboard + analytics
section("Dashboard and analytics")
check("employee sees no analytics feature",
      client.get("/api/dashboard/summary", headers=aditi).get_json()["features"]["analytics"] is False)
check("manager sees analytics feature",
      client.get("/api/dashboard/summary", headers=vikram).get_json()["features"]["analytics"] is True)
mods = [m["key"] for m in client.get("/api/dashboard/summary", headers=aditi).get_json()["modules"]]
check("employee modules are hr + inventory", mods == ["hr", "inventory"], str(mods))
check("employee cannot open analytics", client.get("/api/analytics/summary", headers=aditi).status_code == 403)
check("hr cannot open analytics", client.get("/api/analytics/summary", headers=rahul).status_code == 403)
data = client.get("/api/analytics/summary", headers=admin).get_json()
check("analytics has 14 days of data", len(data["per_day"]) == 14)
check("analytics counts questions", data["totals"]["questions"] > 100)
check("unknown /api path gives 404", client.get("/api/nothing-here").status_code in (404, 401))

# ------------------------------------------------------------------ summary
total = passed + len(failed)
print(f"\n{'=' * 50}\n{passed} of {total} checks passed")
if failed:
    print("Failed:")
    for name in failed:
        print("  -", name)
    sys.exit(1)
print("All good.")