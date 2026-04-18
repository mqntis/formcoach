from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    # TODO: implement user registration
    data = request.get_json()
    return jsonify({"message": "register endpoint placeholder"}), 201


@auth_bp.post("/login")
def login():
    # TODO: implement login and return JWT
    data = request.get_json()
    return jsonify({"message": "login endpoint placeholder"}), 200
