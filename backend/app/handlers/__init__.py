"""
Dispatcher: maps an intent to the module handler that answers it, checks that
the user's role is allowed to use that module, and manages multi-turn context.
"""

from app.handlers import hr, inventory, sales, finance, procurement, approvals
from app.handlers.common import (AccessDenied, make_reply, current_user,
                                 find_item_in_query)
from app.handlers.dialogue import continue_dialogue, detect_followup, remember
from app.nlp.intent_classifier import classify_intent

# intent -> (module, handler function)
ROUTES = {
    "check_leave_balance": ("hr", hr.leave_balance),
    "apply_leave":         ("hr", hr.apply_leave),
    "my_leave_requests":   ("hr", hr.my_leave_requests),
    "employee_info":       ("hr", hr.employee_info),
    "employee_list":       ("hr", hr.employee_list),
    "my_attendance":       ("hr", hr.my_attendance),
    "payslip":             ("hr", hr.payslip),

    "check_inventory":     ("inventory", inventory.check_inventory),
    "low_stock_alert":     ("inventory", inventory.low_stock_alert),
    "inventory_value":     ("inventory", inventory.inventory_value),

    "sales_orders":        ("sales", sales.sales_orders),
    "sales_summary":       ("sales", sales.sales_summary),
    "top_customer":        ("sales", sales.top_customer),

    "overdue_invoices":    ("finance", finance.overdue_invoices),
    "unpaid_invoices":     ("finance", finance.unpaid_invoices),
    "invoice_lookup":      ("finance", finance.invoice_lookup),

    "purchase_orders":     ("procurement", procurement.purchase_orders),

    "pending_approvals":   ("approvals", approvals.pending_approvals),
    "decide_leave":        ("approvals", approvals.decide_leave),
}

# Which modules each role may use
ROLE_MODULES = {
    "employee": {"hr", "inventory"},
    "hr":       {"hr", "inventory", "approvals"},
    "manager":  {"hr", "inventory", "sales", "finance", "procurement", "approvals"},
    "admin":    {"hr", "inventory", "sales", "finance", "procurement", "approvals"},
}

MODULE_LABELS = {"hr": "HR", "inventory": "Inventory", "sales": "Sales",
                 "finance": "Finance", "procurement": "Procurement", "approvals": "Approvals"}

HELP_LINES = {
    "hr": "HR: leave balance, apply leave, leave requests, attendance, payslip, employee info",
    "inventory": "Inventory: stock by item or SKU, low-stock alerts, stock value",
    "sales": "Sales: open orders, order status, sales summary, top customer",
    "finance": "Finance: overdue invoices, unpaid invoices, invoice status",
    "procurement": "Procurement: pending purchase orders, supplier deliveries",
    "approvals": "Approvals: pending approvals, approve or reject a leave request",
}

MODULE_ORDER = ("hr", "inventory", "sales", "finance", "procurement", "approvals")


def _help_text(role):
    modules = [m for m in MODULE_ORDER if m in ROLE_MODULES.get(role, set())]
    return "Here's what you can ask me:\n" + "\n".join(HELP_LINES[m] for m in modules)


def handle(intent, entities, user_id, query):
    """Runs one classified request. Raises AccessDenied if the role is not allowed."""
    user = current_user(user_id)

    if intent == "greeting":
        reply = make_reply(f"Hello, {user.username}! I'm your ERP assistant. Type 'help' to see what I can do.")
        reply["module"] = "general"
        return reply

    if intent == "help":
        reply = make_reply(_help_text(user.role))
        reply["module"] = "general"
        return reply

    if intent in ROUTES:
        module, function = ROUTES[intent]
        if module not in ROLE_MODULES.get(user.role, set()):
            if module == "approvals":
                raise AccessDenied("Only HR, managers and admins can review leave requests. "
                                   "Say 'show my leave requests' to see your own.")
            raise AccessDenied(
                f"Your role ({user.role}) doesn't have access to the {MODULE_LABELS[module]} module. "
                f"Ask a manager or admin.")
        reply = function(entities, user_id, query)
        reply["module"] = module
        return reply

    # Unknown intent: maybe the user just named a product
    if "inventory" in ROLE_MODULES.get(user.role, set()):
        item = find_item_in_query(query)
        if item:
            reply = inventory.check_inventory({}, user_id, query)
            reply["module"] = "inventory"
            return reply

    reply = make_reply("I'm not sure I understood that. Type 'help' to see what I can do.")
    reply["module"] = "general"
    return reply


def process(user_id, query):
    """
    Full pipeline for one chat message.
    Returns (reply, intent, confidence). Access problems become a normal reply.
    """
    intent, confidence = "unknown", 0.0
    try:
        # 1. Is the bot waiting for an answer from the previous turn?
        reply = continue_dialogue(user_id, query)
        if reply is not None:
            reply.setdefault("module", "hr")
            return reply, "dialogue", 1.0

        # 2. Understand the message
        result = classify_intent(query)
        intent, confidence, entities = result["intent"], result["confidence"], result["entities"]
        text = query

        # 3. Is it a follow-up such as "what about employee 2?"
        follow = detect_followup(user_id, query)
        if follow:
            intent, entities, text = follow
            confidence = 1.0

        # 4. Answer it
        reply = handle(intent, entities, user_id, text)

        if reply.get("module") not in ("general", "security") and intent in ROUTES:
            remember(user_id, intent, entities)
        return reply, intent, confidence

    except AccessDenied as e:
        reply = make_reply(e.message)
        reply["module"] = "security"
        return reply, intent, confidence