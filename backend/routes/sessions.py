from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.get("/")
@jwt_required()
def list_sessions():
    # TODO: return user's form coaching sessions
    return jsonify({"sessions": []})


@sessions_bp.post("/")
@jwt_required()
def create_session():
    # TODO: create a new coaching session
    return jsonify({"message": "session created"}), 201
