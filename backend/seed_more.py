"""
Adds sample data for the new modules (Sales, Finance, Procurement, Attendance,
Payroll) plus extra employees and inventory items.

Safe to run more than once: it only inserts rows that are missing.
Run from backend/ :   python seed_more.py
"""

from datetime import date, time, timedelta

from app import create_app, db
from app.models.employee import Employee
from app.models.inventory import InventoryItem
from app.models.hr import Attendance, Payslip
from app.models.sales import Customer, Order
from app.models.finance import Invoice
from app.models.procurement import Supplier, PurchaseOrder

app = create_app()
today = date.today()


def days_ago(n):
    return today - timedelta(days=n)


def month_start(offset):
    """First day of the month, `offset` months before the current one."""
    y, m = today.year, today.month - offset
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


with app.app_context():

    # ---------------- Extra employees (matched by name) ----------------
    extra_employees = [
        ("Neha Kapoor", "Engineering", "Senior Developer", 16),
        ("Vikram Singh", "Sales", "Sales Manager", 12),
        ("Meera Iyer", "Finance", "Finance Analyst", 15),
        ("Arjun Mehta", "Operations", "Warehouse Supervisor", 10),
    ]
    for name, dept, desig, bal in extra_employees:
        if not Employee.query.filter_by(name=name).first():
            next_id = (db.session.query(db.func.max(Employee.id)).scalar() or 0) + 1
            db.session.add(Employee(id=next_id, name=name, department=dept,
                                    designation=desig, leave_balance=bal))
            db.session.flush()
    print("Employees ready.")

    # ---------------- Extra inventory (matched by SKU) ----------------
    extra_items = [
        ("Wireless Mouse", "ABC123", 45, 10, 15.99),
        ("Office Chair", "CHR456", 3, 5, 89.50),
        ("Laptop Stand", "LPS789", 20, 8, 25.00),
        ("Mechanical Keyboard", "KBD101", 4, 10, 49.99),
        ("27 inch Monitor", "MON202", 12, 5, 179.00),
        ("USB-C Hub", "HUB303", 2, 8, 34.50),
        ("Webcam HD", "CAM404", 30, 10, 42.00),
        ("Standing Desk", "DSK505", 6, 4, 320.00),
    ]
    for item_name, sku, qty, reorder, price in extra_items:
        if not InventoryItem.query.filter_by(sku=sku).first():
            db.session.add(InventoryItem(item_name=item_name, sku=sku, quantity=qty,
                                         reorder_level=reorder, unit_price=price))
    print("Inventory ready.")

    # ---------------- Customers ----------------
    customer_rows = [
        ("Acme Corporation", "orders@acme.example", "Mumbai"),
        ("Globex Limited", "buy@globex.example", "Delhi"),
        ("Initech Solutions", "procure@initech.example", "Bengaluru"),
        ("Umbrella Pvt Ltd", "supply@umbrella.example", "Pune"),
        ("Stark Industries", "orders@stark.example", "Chennai"),
    ]
    for name, email, city in customer_rows:
        if not Customer.query.filter_by(name=name).first():
            db.session.add(Customer(name=name, email=email, city=city))
    db.session.flush()
    cust = {c.name: c.id for c in Customer.query.all()}

    # ---------------- Orders + Invoices (only if empty) ----------------
    if Order.query.first() is None:
        order_rows = [
            ("Acme Corporation", 1, 125000, "pending"),
            ("Globex Limited", 2, 84500, "shipped"),
            ("Initech Solutions", 4, 56200, "shipped"),
            ("Umbrella Pvt Ltd", 6, 231000, "delivered"),
            ("Stark Industries", 9, 410000, "delivered"),
            ("Acme Corporation", 12, 78000, "delivered"),
            ("Globex Limited", 15, 33500, "cancelled"),
            ("Initech Solutions", 0, 96000, "pending"),
        ]
        orders = []
        for cname, ago, amount, status in order_rows:
            o = Order(customer_id=cust[cname], order_date=days_ago(ago),
                      total_amount=amount, status=status)
            db.session.add(o)
            orders.append(o)
        db.session.flush()

        # Invoices: some paid, some unpaid, some overdue (unpaid + past due date)
        invoice_plan = [
            (orders[3], "paid", 6, 24),
            (orders[4], "paid", 9, 21),
            (orders[5], "unpaid", 12, -2),    # due 2 days ago -> overdue
            (orders[1], "unpaid", 2, 28),     # not due yet
            (orders[2], "unpaid", 4, 26),     # not due yet
            (orders[0], "unpaid", 1, -5),     # shown as overdue for the demo
        ]
        for o, status, issued_ago, due_in in invoice_plan:
            db.session.add(Invoice(customer_id=o.customer_id, order_id=o.id,
                                   amount=o.total_amount, issue_date=days_ago(issued_ago),
                                   due_date=today + timedelta(days=due_in), status=status))
        print("Orders and invoices seeded.")
    else:
        print("Orders already exist, skipping.")

    # ---------------- Suppliers + Purchase orders ----------------
    supplier_rows = [
        ("TechParts Supplies", "sales@techparts.example", "Noida"),
        ("OfficeWorld Traders", "info@officeworld.example", "Gurugram"),
        ("Prime Electronics", "contact@primeelec.example", "Hyderabad"),
    ]
    for name, email, city in supplier_rows:
        if not Supplier.query.filter_by(name=name).first():
            db.session.add(Supplier(name=name, email=email, city=city))
    db.session.flush()
    sup = {s.name: s.id for s in Supplier.query.all()}

    if PurchaseOrder.query.first() is None:
        po_rows = [
            ("TechParts Supplies", "USB-C Hub", 50, 1725, 3, 7, "pending"),
            ("OfficeWorld Traders", "Office Chair", 20, 1790, 5, 5, "approved"),
            ("Prime Electronics", "Mechanical Keyboard", 40, 1999, 8, -1, "received"),
            ("TechParts Supplies", "27 inch Monitor", 15, 2685, 1, 12, "pending"),
        ]
        for sname, item, qty, cost, ordered_ago, due_in, status in po_rows:
            db.session.add(PurchaseOrder(supplier_id=sup[sname], item_name=item, quantity=qty,
                                         total_cost=cost, order_date=days_ago(ordered_ago),
                                         expected_date=today + timedelta(days=due_in), status=status))
        print("Purchase orders seeded.")
    else:
        print("Purchase orders already exist, skipping.")

    # ---------------- Attendance (last 14 days, weekdays only) ----------------
    if Attendance.query.first() is None:
        employees = Employee.query.order_by(Employee.id).all()
        for idx, emp in enumerate(employees):
            for n in range(0, 14):
                d = days_ago(n)
                if d.weekday() >= 5:      # skip Sat/Sun
                    continue
                if n == 0:
                    status = "present"
                elif (n + idx) % 9 == 0:
                    status = "wfh"
                elif (n + idx) % 13 == 0:
                    status = "absent"
                else:
                    status = "present"
                check_in = None if status == "absent" else time(9, (idx * 7 + n * 3) % 40)
                db.session.add(Attendance(employee_id=emp.id, date=d, status=status, check_in=check_in))
        print("Attendance seeded.")
    else:
        print("Attendance already exists, skipping.")

    # ---------------- Payslips (last 3 months) ----------------
    if Payslip.query.first() is None:
        basic_by_designation_default = 45000
        for emp in Employee.query.order_by(Employee.id).all():
            basic = {1: 60000, 2: 75000, 12: 50000}.get(emp.id, basic_by_designation_default)
            allowances = round(basic * 0.20)
            deductions = round(basic * 0.10)
            for offset in (0, 1, 2):
                start = month_start(offset)
                db.session.add(Payslip(
                    employee_id=emp.id, month_label=start.strftime("%B %Y"), period_start=start,
                    basic=basic, allowances=allowances, deductions=deductions,
                    net_pay=basic + allowances - deductions))
        print("Payslips seeded.")
    else:
        print("Payslips already exist, skipping.")

    db.session.commit()
    print("Done. All modules seeded.")