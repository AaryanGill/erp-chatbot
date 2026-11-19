"""Approvals module: HR, managers and admins review leave requests."""

import re

from app import db
from app.models.employee import Employee, LeaveRequest
from app.handlers.common import AccessDenied, make_reply, current_user


def pending_approvals(entities, user_id, query):
    user = current_user(user_id)
    requests_ = (LeaveRequest.query.filter_by(status="pending")
                 .order_by(LeaveRequest.created_at).all())
    if not requests_:
        return make_reply("No leave requests are waiting for approval.")

    employees = {e.id: e for e in Employee.query.filter(
        Employee.id.in_([r.employee_id for r in requests_])).all()}
    rows = []
    for r in requests_[:10]:
        emp = employees.get(r.employee_id)
        name = emp.name if emp else "Unknown"
        if emp and emp.user_id == user.id:
            name += " (you)"
        rows.append([f"#{r.id}", name, str(r.start_date), str(r.end_date),
                     str((r.end_date - r.start_date).days + 1)])
    return make_reply(
        f"{len(requests_)} leave request(s) are waiting for approval. "
        f"Say 'approve request <number>' or 'reject request <number>'.",
        ["Request", "Employee", "From", "To", "Days"], rows)


def decide_leave(entities, user_id, query):
    request_id = entities.get("request_id")
    if not request_id:
        return make_reply("Which request? For example: 'approve request 3'. "
                          "Say 'pending approvals' to see the list.")

    req = LeaveRequest.query.get(int(request_id))
    if not req:
        return make_reply(f"No leave request found with number {request_id}.")

    emp = Employee.query.get(req.employee_id)
    user = current_user(user_id)
    if emp and emp.user_id == user.id:
        raise AccessDenied("You can't approve or reject your own leave request.")
    if req.status != "pending":
        return make_reply(f"Request #{req.id} is already {req.status}.")

    days = (req.end_date - req.start_date).days + 1
    who = emp.name if emp else "the employee"

    if re.search(r"\b(reject|decline|deny)", query, re.I):
        req.status = "rejected"
        if emp:
            emp.leave_balance += days          # give the days back
        db.session.commit()
        return make_reply(f"Request #{req.id} from {who} ({req.start_date} to {req.end_date}) "
                          f"has been rejected. {days} day(s) were returned to their leave balance.")

    req.status = "approved"
    db.session.commit()
    return make_reply(f"Request #{req.id} from {who} ({req.start_date} to {req.end_date}, "
                      f"{days} day(s)) has been approved.")