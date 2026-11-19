"""Shared helpers used by every module handler."""

import re

from app import db
from app.models.user import User
from app.models.employee import Employee
from app.models.inventory import InventoryItem
from app.models.sales import Customer
from app.models.procurement import Supplier

NO_RECORD = "I couldn't find your employee record. Try specifying an employee ID."


class AccessDenied(Exception):
    """Raised when the logged-in user is not allowed to do something."""

    def __init__(self, message="Access denied."):
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------- replies
def make_reply(summary, columns=None, rows=None):
    """A reply is a short summary sentence plus an optional table."""
    table = {"columns": columns, "rows": rows} if columns and rows else None
    return {"summary": summary, "table": table}


def reply_to_text(reply):
    """Plain-text version (used by simple UIs and chat logs)."""
    text = reply["summary"]
    table = reply.get("table")
    if table:
        lines = [" | ".join(table["columns"])]
        lines += [" | ".join(str(c) for c in row) for row in table["rows"]]
        text += "\n" + "\n".join(lines)
    return text


def inr(amount, decimals=0):
    """Formats a number in Indian style: 125000 -> ₹1,25,000"""
    value = round(abs(float(amount or 0)), decimals)
    sign = "-" if float(amount or 0) < 0 else ""
    whole = int(value)
    frac = f"{value - whole:.{decimals}f}"[1:] if decimals else ""
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups + [tail])
    return f"{sign}₹{s}{frac}"


# ---------------------------------------------------------------- users
def current_user(user_id):
    return User.query.get(int(user_id))


def resolve_employee(entities: dict, user_id):
    """
    No employee ID in the query -> the logged-in user's own record.
    Employee ID given -> allowed only for hr/admin, or if it is the user's own record.
    """
    user = current_user(user_id)
    own = Employee.query.filter_by(user_id=user.id).first()

    emp_id = entities.get("employee_id")
    if not emp_id:
        return own

    target = Employee.query.get(emp_id)
    if user.role in ("hr", "admin"):
        return target
    if own and target and own.id == target.id:
        return target
    raise AccessDenied("You can only view your own HR records. "
                       "HR and admin accounts can look up other employees.")


# ---------------------------------------------------------------- name matching
def _name_in_query(name: str, q: str, min_len=4):
    """True if the full name, or its first distinctive word, appears in the query."""
    n = name.lower()
    if n in q:
        return True
    first = re.findall(r"[a-z0-9]+", n)[0]
    return len(first) >= min_len and re.search(rf"\b{re.escape(first)}", q) is not None


def find_customer_in_query(query: str):
    q = query.lower()
    for c in Customer.query.all():
        if _name_in_query(c.name, q):
            return c
    return None


def find_supplier_in_query(query: str):
    q = query.lower()
    for s in Supplier.query.all():
        if _name_in_query(s.name, q):
            return s
    return None


def find_item_in_query(query: str):
    """Finds an inventory item whose name (or a main word of it) appears in the query."""
    q = query.lower()
    items = InventoryItem.query.all()
    for item in items:
        if item.item_name.lower() in q:
            return item
    for item in items:
        words = [w for w in re.findall(r"[a-z]+", item.item_name.lower()) if len(w) > 3]
        if any(w in q for w in words):
            return item
    return None