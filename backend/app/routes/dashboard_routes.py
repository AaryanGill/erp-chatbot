"""
Dashboard data for the React interface:
  * the user's name and role
  * KPI cards that suit their role
  * the modules they may use, each with quick-action buttons
"""

from datetime import date

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.models.employee import Employee, LeaveRequest
from app.models.inventory import InventoryItem
from app.models.sales import Order
from app.models.finance import Invoice
from app.models.procurement import PurchaseOrder
from app.handlers import ROLE_MODULES, MODULE_LABELS, MODULE_ORDER
from app.handlers.common import inr

dashboard_bp = Blueprint("dashboard", __name__)

# Quick-action buttons shown for each module: (label, message sent to the chatbot)
MODULE_ACTIONS = {
    "hr": [
        ("Leave balance", "check leave balance"),
        ("Apply for leave", "apply leave"),
        ("My leave requests", "show my leave requests"),
        ("My attendance", "show my attendance"),
        ("My payslip", "show my payslip"),
        ("My profile", "show my employee profile"),
    ],
    "inventory": [
        ("Low stock items", "what items are low on stock"),
        ("Stock value", "total stock value"),
        ("Check by SKU", "check stock for SKU ABC123"),
    ],
    "sales": [
        ("Open orders", "show open orders"),
        ("Sales summary", "sales summary"),
        ("Top customer", "who is our top customer"),
    ],
    "finance": [
        ("Overdue invoices", "show overdue invoices"),
        ("Unpaid invoices", "show unpaid invoices"),
        ("Latest invoices", "show latest invoices"),
    ],
    "procurement": [
        ("Pending purchase orders", "show pending purchase orders"),
        ("Supplier deliveries", "which deliveries are pending"),
    ],
    "approvals": [
        ("Pending approvals", "show pending approvals"),
    ],
}


def _kpis(user, own):
    modules = ROLE_MODULES.get(user.role, set())
    today = date.today()
    cards = []

    if own:
        cards.append({"key": "leave", "label": "Leave balance", "value": f"{own.leave_balance} days",
                      "hint": "Available to take", "message": "check leave balance"})

    if "approvals" in modules:
        n = LeaveRequest.query.filter_by(status="pending").count()
        cards.append({"key": "approvals", "label": "Awaiting approval", "value": str(n),
                      "hint": "Leave requests", "message": "show pending approvals"})
    elif own:
        n = LeaveRequest.query.filter_by(employee_id=own.id, status="pending").count()
        cards.append({"key": "mine", "label": "My pending requests", "value": str(n),
                      "hint": "Waiting for approval", "message": "show my leave requests"})

    if user.role in ("hr", "admin"):
        cards.append({"key": "staff", "label": "Employees", "value": str(Employee.query.count()),
                      "hint": "On the payroll", "message": "list all employees"})

    if "sales" in modules:
        open_orders = Order.query.filter(Order.status.in_(["pending", "shipped"])).all()
        total = sum(float(o.total_amount) for o in open_orders)
        cards.append({"key": "orders", "label": "Open orders", "value": str(len(open_orders)),
                      "hint": f"Worth {inr(total)}", "message": "show open orders"})

    if "finance" in modules:
        overdue = Invoice.query.filter(Invoice.status == "unpaid", Invoice.due_date < today).all()
        total = sum(float(i.amount) for i in overdue)
        cards.append({"key": "overdue", "label": "Overdue invoices", "value": str(len(overdue)),
                      "hint": f"{inr(total)} outstanding", "message": "show overdue invoices"})

    if "procurement" in modules:
        n = PurchaseOrder.query.filter(PurchaseOrder.status != "received").count()
        cards.append({"key": "pos", "label": "Pending deliveries", "value": str(n),
                      "hint": "Purchase orders", "message": "show pending purchase orders"})

    if "inventory" in modules:
        n = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.reorder_level).count()
        cards.append({"key": "stock", "label": "Low stock items", "value": str(n),
                      "hint": "At or below reorder level", "message": "what items are low on stock"})

    return cards[:5]


@dashboard_bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    user = User.query.get(int(get_jwt_identity()))
    own = Employee.query.filter_by(user_id=user.id).first()
    allowed = ROLE_MODULES.get(user.role, set())

    modules = []
    for key in MODULE_ORDER:
        if key not in allowed:
            continue
        actions = MODULE_ACTIONS[key]
        if key == "hr" and user.role in ("hr", "admin"):
            actions = actions + [("All employees", "list all employees")]
        if key == "hr" and not own:
            actions = [a for a in actions if a[0] in ("All employees",)] or actions[:0]
        modules.append({"key": key, "label": MODULE_LABELS[key],
                        "actions": [{"label": l, "message": m} for l, m in actions]})

    return jsonify({
        "user": {"username": user.username, "role": user.role,
                 "name": own.name if own else user.username},
        "kpis": _kpis(user, own),
        "modules": modules,
        "features": {"analytics": user.role in ("manager", "admin")},
    })