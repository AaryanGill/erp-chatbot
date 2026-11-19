from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app import db
from app.models.user import User
from app.models.employee import Employee

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 409

    user = User(username=data["username"], email=data["email"], role="employee")
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()  # gives user.id before commit

    # Every new user also gets an employee record, so the chatbot can find "their" data.
    # We compute the next id manually because the seed script inserted fixed ids (1, 2, 12).
    next_id = (db.session.query(db.func.max(Employee.id)).scalar() or 0) + 1
    employee = Employee(
        id=next_id,
        name=data["username"],
        department="General",
        designation="Employee",
        leave_balance=18,
        user_id=user.id,
    )
    db.session.add(employee)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get("username")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401

    from app.handlers.dialogue import clear_user
    clear_user(user.id)          # start every login with a clean conversation

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})