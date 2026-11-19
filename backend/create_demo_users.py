"""
Creates demo accounts with different roles, linked to employee records.

  aditi   (employee) -> Aditi Sharma
  rahul   (hr)       -> Rahul Verma
  vikram  (manager)  -> Vikram Singh
  admin   (admin)    -> no employee record

New accounts get the password  test123 .  Existing accounts keep their password
but their role and employee link are corrected.

Run from backend/ :   python create_demo_users.py
"""

from app import create_app, db
from app.models.user import User
from app.models.employee import Employee

app = create_app()

DEMO_USERS = [
    ("aditi", "aditi@example.com", "employee", "Aditi Sharma"),
    ("rahul", "rahul@example.com", "hr", "Rahul Verma"),
    ("vikram", "vikram@example.com", "manager", "Vikram Singh"),
    ("admin", "admin@example.com", "admin", None),
]

with app.app_context():
    for username, email, role, employee_name in DEMO_USERS:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, email=email, role=role)
            user.set_password("test123")
            db.session.add(user)
            created = "created"
        else:
            user.role = role
            created = "updated"
        db.session.flush()

        linked = ""
        if employee_name:
            emp = Employee.query.filter_by(name=employee_name).first()
            if emp:
                emp.user_id = user.id
                linked = f" -> linked to {employee_name}"
            else:
                linked = f" (employee '{employee_name}' not found)"
        print(f"{username:8s} {role:9s} {created}{linked}")

    db.session.commit()
    print("Done. Password for new accounts: test123")