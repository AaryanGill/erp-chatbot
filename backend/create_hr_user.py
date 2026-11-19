"""
Creates (or upgrades) an HR user linked to Rahul Verma (employee id 2).
Run once:  python create_hr_user.py
"""

from app import create_app, db
from app.models.user import User
from app.models.employee import Employee

app = create_app()

with app.app_context():
    user = User.query.filter_by(username="rahul").first()
    if not user:
        user = User(username="rahul", email="rahul@example.com", role="hr")
        user.set_password("test123")
        db.session.add(user)
        db.session.flush()
    else:
        user.role = "hr"

    # Unlink any other employee record that points to this user
    Employee.query.filter(Employee.user_id == user.id, Employee.id != 2).update({"user_id": None})

    emp = Employee.query.get(2)
    if emp:
        emp.user_id = user.id

    db.session.commit()
    print("HR user ready -> username: rahul / password: test123")