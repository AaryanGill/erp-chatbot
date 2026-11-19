"""
Measures classifier accuracy on sentences NOT used in training.
Run from backend/:  python evaluate_nlp.py
"""
from app.nlp.intent_classifier import classify_intent

TEST_SET = [
    # HR
    ("how many leave days do i have", "check_leave_balance"),
    ("what is my remaining leave", "check_leave_balance"),
    ("i would like to apply for leave on 3 december", "apply_leave"),
    ("please book a vacation for me tomorrow", "apply_leave"),
    ("show my pending leave requests", "my_leave_requests"),
    ("give me details of employee 2", "employee_info"),
    ("show my profile details", "employee_info"),
    ("show me all the employees", "employee_list"),
    ("which employees work in finance", "employee_list"),
    ("was i present today", "my_attendance"),
    ("show my attendance for the last week", "my_attendance"),
    ("how much salary do i get", "payslip"),
    ("show my salary slip", "payslip"),
    ("what was my net pay in october", "payslip"),
    # Inventory
    ("how many wireless mouse do we have", "check_inventory"),
    ("is sku lps789 in stock", "check_inventory"),
    ("which items are running low", "low_stock_alert"),
    ("show items to reorder", "low_stock_alert"),
    ("what is our inventory worth", "inventory_value"),
    ("total value of the stock", "inventory_value"),
    # Sales
    ("show me the open orders", "sales_orders"),
    ("what is the status of order 5", "sales_orders"),
    ("orders placed by stark industries", "sales_orders"),
    ("how much revenue did we generate", "sales_summary"),
    ("show me the sales report", "sales_summary"),
    ("who is our biggest customer", "top_customer"),
    ("which client spends the most", "top_customer"),
    # Finance
    ("which invoices are overdue", "overdue_invoices"),
    ("any late payments", "overdue_invoices"),
    ("how much money are customers yet to pay", "unpaid_invoices"),
    ("show the outstanding amount", "unpaid_invoices"),
    ("is invoice 4 paid", "invoice_lookup"),
    ("invoices of umbrella", "invoice_lookup"),
    # Procurement
    ("show pending purchase orders", "purchase_orders"),
    ("when will the monitors arrive from the supplier", "purchase_orders"),
    ("status of po 3", "purchase_orders"),
    # Approvals
    ("approve request 7", "decide_leave"),
    ("please reject leave request 2", "decide_leave"),
    ("what leave requests are waiting for approval", "pending_approvals"),
    ("show me pending approvals", "pending_approvals"),
    ("show pending leave requests", "pending_approvals"),
    ("did my leave get approved", "my_leave_requests"),
    # General
    ("hey there", "greeting"),
    ("good evening", "greeting"),
    ("what can this bot do", "help"),
    ("show me the available commands", "help"),
    # Out of scope
    ("what is the capital of france", "unknown"),
    ("tell me a joke", "unknown"),
    ("play some music", "unknown"),
]

correct = 0
for text, expected in TEST_SET:
    r = classify_intent(text)
    got = r["intent"]
    ok = got == expected
    correct += ok
    if not ok:
        print(f"FAIL {text!r:55} expected={expected:20} got={got} ({r['method']} {r['confidence']})")

print(f"\nAccuracy: {correct}/{len(TEST_SET)} = {100*correct/len(TEST_SET):.1f}%")