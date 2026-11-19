from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.chat_log import ChatLog
from app.handlers import process
from app.handlers.common import make_reply, reply_to_text

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/message", methods=["POST"])
@jwt_required()
def handle_message():
    data = request.get_json() or {}
    user_query = data.get("message", "").strip()
    if not user_query:
        return jsonify({"error": "message field is required"}), 400

    current_user_id = get_jwt_identity()

    try:
        reply, intent, confidence = process(current_user_id, user_query)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Error while handling chat message")
        reply = make_reply("Something went wrong while processing that request.")
        reply["module"] = "general"
        intent, confidence = "error", 0.0

    text = reply_to_text(reply)

    db.session.add(ChatLog(user_id=current_user_id, query=user_query,
                           detected_intent=intent, response=text))
    db.session.commit()

    return jsonify({
        "reply": text,                    # plain text (works in any UI)
        "summary": reply["summary"],      # one-line summary
        "table": reply["table"],          # {"columns": [...], "rows": [[...]]} or null
        "module": reply.get("module"),
        "intent": intent,
        "confidence": confidence,
    })