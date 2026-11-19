"""HR module: leave, attendance, payslips, employee directory."""

import re
from datetime import date, timedelta

from app import db
from app.models.employee import Employee, LeaveRequest
from app.models.hr import Attendance, Payslip
from app.nlp.date_parser import extract_dates
from app.handlers.dialogue import set_state
from app.handlers.common import AccessDenied, make_reply, resolve_employee, current_user, inr, NO_RECORD

STATUS_LABEL = {"present": "Present", "wfh": "Work from home", "absent": "Absent", "leave": "On leave"}

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"]


def leave_balance(entities, user_id, query):
    emp = resolve_employee(entities, user_id)
    if not emp:
        return make_reply(NO_RECORD)
    return make_reply(f"{emp.name} has {emp.leave_balance} leave day(s) remaining.")


def plan_leave(emp, dates, user_id):
    """Checks the requested dates, then asks the user to confirm."""
    today = date.today()
    if len(dates) == 1:
        start = end = dates[0]
    else:
        start, end = dates[0], dates[1]

    if end < start:
        return make_reply("The end date can't be before the start date.")
    if start <= today:
        return make_reply("Leave must start from tomorrow or a later date.")

    days = (end - start).days + 1
    if days > emp.leave_balance:
        return make_reply(f"You asked for {days} day(s) but {emp.name} only has "
                          f"{emp.leave_balance} day(s) remaining.")

    set_state(user_id, "leave_confirm", {
        "employee_id": emp.id, "start": start.isoformat(),
        "end": end.isoformat(), "days": days})
    return make_reply(
        f"Apply for {days} day(s) of leave for {emp.name} from {start} to {end}? "
        f"The balance would go from {emp.leave_balance} to {emp.leave_balance - days}. "
        f"Reply 'yes' to confirm or 'no' to cancel.")


def commit_leave(data):
    """Runs after the user confirms: saves the request and updates the balance."""
    emp = Employee.query.get(data["employee_id"])
    days = data["days"]
    if not emp or days > emp.leave_balance:
        return make_reply("Sorry, that request can no longer be submitted. "
                          "Please check the balance and try again.")

    request_row = LeaveRequest(employee_id=emp.id,
                               start_date=date.fromisoformat(data["start"]),
                               end_date=date.fromisoformat(data["end"]),
                               status="pending")
    db.session.add(request_row)
    emp.leave_balance -= days
    db.session.commit()
    return make_reply(f"Leave request #{request_row.id} submitted for {emp.name} "
                      f"({data['start']} to {data['end']}, {days} day(s)). "
                      f"Remaining balance: {emp.leave_balance} day(s). Status: pending approval.")


def apply_leave(entities, user_id, query):
    emp = resolve_employee(entities, user_id)
    if not emp:
        return make_reply(NO_RECORD)

    dates = extract_dates(query, date.today())
    if not dates:
        set_state(user_id, "leave_dates", {"employee_id": emp.id})
        return make_reply(f"Which dates would you like off, {emp.name.split()[0]}? "
                          f"For example: 'from 5 Nov to 8 Nov', 'on 20 Dec' or 'tomorrow'.")
    return plan_leave(emp, dates, user_id)

def my_leave_requests(entities, user_id, query):
    emp = resolve_employee(entities, user_id)
    if not emp:
        return make_reply(NO_RECORD)

    items = (LeaveRequest.query.filter_by(employee_id=emp.id)
             .order_by(LeaveRequest.created_at.desc()).limit(5).all())
    if not items:
        return make_reply(f"{emp.name} has no leave requests yet.")

    rows = [[str(r.id), str(r.start_date), str(r.end_date),
             str((r.end_date - r.start_date).days + 1), r.status.title()] for r in items]
    return make_reply(f"Latest leave requests for {emp.name}:",
                      ["Request", "From", "To", "Days", "Status"], rows)


def employee_info(entities, user_id, query):
    emp = resolve_employee(entities, user_id)
    if not emp:
        return make_reply(NO_RECORD)
    rows = [["Employee ID", str(emp.id)], ["Department", emp.department or "-"],
            ["Designation", emp.designation or "-"], ["Leave balance", f"{emp.leave_balance} days"]]
    return make_reply(f"{emp.name} — {emp.designation}, {emp.department} department.",
                      ["Field", "Value"], rows)


def employee_list(entities, user_id, query):
    user = current_user(user_id)
    if user.role not in ("hr", "admin"):
        raise AccessDenied("Only HR and admin accounts can list employees.")

    q = query.lower()
    departments = [d for (d,) in db.session.query(Employee.department).distinct() if d]
    chosen = [d for d in departments if d.lower() in q]

    base = Employee.query
    if chosen:
        base = base.filter(Employee.department.in_(chosen))
    total = base.count()
    employees = base.order_by(Employee.id).limit(15).all()
    if not employees:
        return make_reply("No employees found.")

    label = f" in {', '.join(chosen)}" if chosen else ""
    summary = f"{total} employee(s){label}." + (" Showing the first 15." if total > 15 else "")
    rows = [[str(e.id), e.name, e.department or "-", e.designation or "-", str(e.leave_balance)]
            for e in employees]
    return make_reply(summary, ["ID", "Name", "Department", "Designation", "Leave left"], rows)


def my_attendance(entities, user_id, query):
    emp = resolve_employee(entities, user_id)
    if not emp:
        return make_reply(NO_RECORD)

    today = date.today()
    q = query.lower()

    if "today" in q:
        rec = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
        if not rec:
            return make_reply(f"No attendance is marked for {emp.name} today.")
        when = f" (check-in {rec.check_in.strftime('%H:%M')})" if rec.check_in else ""
        return make_reply(f"{emp.name} is marked '{STATUS_LABEL.get(rec.status, rec.status)}' today{when}.")

    records = (Attendance.query
               .filter(Attendance.employee_id == emp.id, Attendance.date >= today - timedelta(days=13))
               .order_by(Attendance.date.desc()).all())
    if not records:
        return make_reply(f"No attendance records found for {emp.name}.")

    counts = {"present": 0, "wfh": 0, "absent": 0}
    for r in records:
        if r.status in counts:
            counts[r.status] += 1

    rows = [[r.date.strftime("%a %d %b"), STATUS_LABEL.get(r.status, r.status),
             r.check_in.strftime("%H:%M") if r.check_in else "-"] for r in records[:7]]
    summary = (f"Last 14 days for {emp.name}: {counts['present']} present, "
               f"{counts['wfh']} work from home, {counts['absent']} absent.")
    return make_reply(summary, ["Date", "Status", "Check-in"], rows)


def payslip(entities, user_id, query):
    emp = resolve_employee(entities, user_id)
    if not emp:
        return make_reply(NO_RECORD)

    q = query.lower()
    slips = Payslip.query.filter_by(employee_id=emp.id).order_by(Payslip.period_start.desc()).all()
    if not slips:
        return make_reply(f"No payslips found for {emp.name}.")

    chosen = None
    for name in MONTH_NAMES:
        short = name[:3]
        if re.search(rf"\b{name}\b", q) or (short != "may" and re.search(rf"\b{short}\b", q)) \
                or (short == "may" and re.search(r"\b(for|in|of)\s+may\b", q)):
            chosen = next((s for s in slips if s.month_label.lower().startswith(name)), None)
            break
    if chosen is None:
        chosen = slips[1] if "last month" in q and len(slips) > 1 else slips[0]

    rows = [["Basic", inr(chosen.basic)], ["Allowances", inr(chosen.allowances)],
            ["Deductions", "-" + inr(chosen.deductions)], ["Net pay", inr(chosen.net_pay)]]
    return make_reply(f"{emp.name}'s net pay for {chosen.month_label} is {inr(chosen.net_pay)}.",
                      ["Component", "Amount"], rows)