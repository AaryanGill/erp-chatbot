# Nexa ERP – Intelligent ERP Chatbot

A conversational assistant for ERP systems. Users type normal sentences ("how many leave days do I have left", "show overdue invoices") and the system understands the request with NLP and machine learning, checks the user's permissions, reads or updates a PostgreSQL ERP database, and replies with a clear answer or table.

**Stack:** React (Vite) · Flask · PostgreSQL · NLTK · scikit-learn · JWT authentication

---

## Features

- **Six ERP areas in one chat:** HR (leave, attendance, payslips, employee directory), Inventory, Sales, Finance, Procurement and Approvals
- **Hybrid NLP engine:** priority patterns, a trained TF-IDF + Logistic Regression model, and a keyword fallback; out-of-scope questions are rejected instead of guessed
- **Reads and writes:** applies for leave (with a confirmation step), approves or rejects requests (returning days on rejection)
- **Conversation memory:** asks for missing dates, confirms before saving, and understands follow-ups such as "what about employee 2?"
- **Security:** JWT login, hashed passwords, role-based access control (employee, hr, manager, admin) enforced on the server, and no self-approval of leave
- **Modern interface:** glass-style design, live KPI cards, tables with status badges, dark mode
- **Analytics page** (managers and admins): usage per day, per module, most-asked and not-understood questions

---

## Project structure

```
Major Project/
├── backend/
│   ├── run.py                    start the API
│   ├── seed.py                   base employees and inventory
│   ├── seed_more.py              sales, finance, procurement, attendance, payroll data
│   ├── create_demo_users.py      demo accounts for every role
│   ├── seed_chat_history.py      demo chat history for the analytics page
│   ├── evaluate_nlp.py           measures classifier accuracy
│   ├── reset_demo.py             puts demo data back to a clean state
│   ├── tests/run_tests.py        65 automated end-to-end checks
│   ├── requirements.txt
│   ├── .env                      database URL and secret key (not committed)
│   └── app/
│       ├── models/               database tables
│       ├── nlp/                  intent classifier, ML model, training data, date parser
│       ├── handlers/             one file per ERP module + dialogue memory
│       └── routes/               auth, chat, dashboard, analytics endpoints
└── frontend/
    └── src/
        ├── components/           Login, Sidebar, KpiCards, ChatPanel, DataTable, Analytics
        ├── hooks/useChat.js
        └── services/api.js
```

---

## 1. Requirements

- Python 3.10 or newer
- Node.js 18 or newer
- PostgreSQL 14 or newer (the project was built on PostgreSQL 18)

## 2. Create the database (once)

Open **SQL Shell (psql)** as the `postgres` user and run:

```sql
CREATE USER erp_user WITH PASSWORD 'test123';
CREATE DATABASE erp_chatbot_db OWNER erp_user;
GRANT ALL PRIVILEGES ON DATABASE erp_chatbot_db TO erp_user;
```

## 3. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql://erp_user:test123@localhost:5432/erp_chatbot_db
JWT_SECRET_KEY=change-this-to-a-long-random-string
FLASK_DEBUG=True
```

Create the tables and load demo data. **Run these in order, once:**

```powershell
python seed.py
python seed_more.py
python create_demo_users.py
python seed_chat_history.py
```

Start the API:

```powershell
python run.py
```

It runs at http://127.0.0.1:5000. The first start downloads a few small NLTK data files, so an internet connection is needed once.

## 4. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

## 5. One-command mode (best for demos)

Build the interface once, and Flask will serve it too, so you only need **one** terminal:

```powershell
cd frontend
npm run build
cd ..\backend
python run.py
```

Open **http://localhost:5000**. (Use `npm run dev` and port 5173 only while you are changing the interface.)

---

## Demo accounts

All demo passwords are `test123`.

| Username | Role | Can use |
|---|---|---|
| `aditi` | employee | Own HR data, inventory |
| `rahul` | hr | All employees' HR data, inventory, approvals |
| `vikram` | manager | Sales, finance, procurement, inventory, approvals, analytics |
| `admin` | admin | Everything |

## Things to ask

| Area | Examples |
|---|---|
| HR | `check leave balance` · `apply leave` · `show my payslip` · `show my attendance` · `list all employees` |
| Inventory | `what items are low on stock` · `total stock value` · `check stock for SKU ABC123` |
| Sales | `show open orders` · `orders from acme` · `sales summary` · `who is our top customer` |
| Finance | `show overdue invoices` · `unpaid invoices` · `status of invoice 3` |
| Procurement | `pending purchase orders` · `when will the usb-c hub arrive` |
| Approvals | `pending approvals` · `approve request 1` · `reject request 2` |
| Follow-ups | `show invoices for globex`, then `what about acme` |

Try the same question under different accounts to see role-based access in action.

---

## Automated tests

```powershell
cd backend
python tests/run_tests.py
```

Runs 65 checks (login, language understanding, leave flow with confirmation, approvals, access control, follow-ups, dashboard, analytics). It uses a temporary SQLite database, so your real PostgreSQL data is never touched. Expected last line: `65 of 65 checks passed`.

## Reset before a presentation

```powershell
cd backend
python reset_demo.py
```

Clears leave requests and chat history, restores leave balances and the demo passwords (`test123`), and refills the analytics history. Orders, invoices, stock and accounts are left alone.

## Checking the NLP accuracy

```powershell
cd backend
python evaluate_nlp.py
```

To improve the assistant, add example sentences to `backend/app/nlp/training_data.py` (the Analytics page lists real questions it did not understand) and run the evaluation again.

## Backing up the database

```powershell
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U erp_user -h localhost erp_chatbot_db -f erp_backup.sql
```

Restore on another machine with `psql -U erp_user -h localhost -d erp_chatbot_db -f erp_backup.sql`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `password authentication failed` | Re-run the `CREATE USER` line, or `ALTER USER erp_user WITH PASSWORD 'test123';` as `postgres` |
| Chat says it cannot reach the server | The backend is not running. Start `python run.py` |
| Page looks unstyled | Check that `src/main.jsx` imports both `index.css` and `App.css` and that `App.css` contains the project styles (not the Vite default) |
| Signed out straight after login | Clear site data for localhost in the browser (F12, Application, Local Storage) |
| VS Code underlines `flask` or `nltk` | Select the interpreter: Ctrl+Shift+P, then `Python: Select Interpreter`, then `backend\venv\Scripts\python.exe` |
| Analytics page missing | It only appears for the `manager` and `admin` roles |

---

## Known limitations

- The assistant is trained on about 330 example sentences, so unusual wording may not be understood
- Conversation memory is held in the server's RAM and resets when the backend restarts
- Only leave requests go through an approval workflow
- Money values use the Indian rupee format and are sample data

## Future work

Larger training set or a transformer-based classifier, memory stored in Redis or the database, approval flows for purchase orders, email notifications, and a production deployment (Gunicorn, managed PostgreSQL, HTTPS).
