"""
Populates the database with sample ERP data for testing the chatbot.
Run this once after the server has started (so tables already exist).
"""

from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.inventory import InventoryItem

app = create_app()

with app.app_context():
    # --- Users ---
    if User.query.filter_by(username="aditi").first() is None:
        user1 = User(username="aditi", email="aditi@example.com", role="employee")
        user1.set_password("test123")
        db.session.add(user1)
        db.session.flush()  # so user1.id is available before commit
    else:
        user1 = User.query.filter_by(username="aditi").first()

    # --- Employees (linked to users via user_id) ---
    if Employee.query.first() is None:
        employees = [
            Employee(id=1, name="Aditi Sharma", department="Engineering", designation="Software Engineer",
                      leave_balance=14, user_id=user1.id),
            Employee(id=2, name="Rahul Verma", department="HR", designation="HR Manager", leave_balance=20),
            Employee(id=12, name="Priya Nair", department="Finance", designation="Accountant", leave_balance=9),
        ]
        db.session.bulk_save_objects(employees)
        print("Seeded employees.")
    else:
        print("Employees already exist, skipping.")

    if InventoryItem.query.first() is None:
        items = [
            InventoryItem(item_name="Wireless Mouse", sku="ABC123", quantity=45, reorder_level=10, unit_price=15.99),
            InventoryItem(item_name="Office Chair", sku="CHR456", quantity=3, reorder_level=5, unit_price=89.50),
            InventoryItem(item_name="Laptop Stand", sku="LPS789", quantity=20, reorder_level=8, unit_price=25.00),
        ]
        db.session.bulk_save_objects(items)
        print("Seeded inventory items.")
    else:
        print("Inventory items already exist, skipping.")

    db.session.commit()
    print("Done.")