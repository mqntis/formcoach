from flask import Blueprint, request, jsonify
from services.butterbase import (
    list_sessions, get_session, create_session, update_session,
    request_download_url, ButterbaseError,
)

results_bp = Blueprint("results", __name__)

sessions_bp = Blueprint("sessions", __name__)


def _error(msg: str, status: int):
    return jsonify({"error": msg}), status


@sessions_bp.get("/")
def get_sessions():
    phone = request.args.get("phone_number")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    try:
        rows = list_sessions(phone_number=phone, limit=limit, offset=offset)
        return jsonify({"sessions": rows})
    except ButterbaseError as e:
        return _error(str(e), e.status_code)


@sessions_bp.get("/<session_id>")
def get_session_by_id(session_id: str):
    try:
        return jsonify(get_session(session_id))
    except ButterbaseError as e:
        return _error(str(e), e.status_code)


@sessions_bp.post("/")
def post_session():
    data = request.get_json(silent=True) or {}
    try:
        row = create_session(data)
        return jsonify(row), 201
    except ButterbaseError as e:
        return _error(str(e), e.status_code)


@sessions_bp.patch("/<session_id>")
def patch_session(session_id: str):
    data = request.get_json(silent=True) or {}
    try:
        row = update_session(session_id, data)
        return jsonify(row)
    except ButterbaseError as e:
        return _error(str(e), e.status_code)


@results_bp.get("/<session_id>")
def get_results(session_id: str):
    """
    GET /api/get-results/<session_id>
    Returns all session fields plus fresh presigned download URLs for stored video object IDs.
    """
    try:
        session = get_session(session_id)
    except ButterbaseError as e:
        return _error(str(e), e.status_code)

    video_fields = ("original_video_url", "raw_seadance_url", "conditioned_seadance_url")
    download_urls = {}
    for field in video_fields:
        object_id = session.get(field)
        if object_id:
            try:
                result = request_download_url(object_id)
                download_urls[field] = result.get("downloadUrl")
            except ButterbaseError:
                download_urls[field] = None

    return jsonify({
        "session_id":               session.get("session_id"),
        "phone_number":             session.get("phone_number"),
        "original_video_url":       download_urls.get("original_video_url"),
        "raw_seadance_url":         session.get("raw_seadance_url"),
        "conditioned_seadance_url": session.get("conditioned_seadance_url"),
        "joint_data":               session.get("joint_data"),
        "correction_text":          session.get("correction_text"),
        "verified_correction":      session.get("verified_correction"),
        "created_at":               session.get("created_at"),
    })


@sessions_bp.get("/<session_id>/download-url/<field>")
def get_field_download_url(session_id: str, field: str):
    """Return a fresh presigned download URL for one of the video object IDs on a session."""
    video_fields = {"original_video_url", "raw_seadance_url", "conditioned_seadance_url"}
    if field not in video_fields:
        return _error(f"field must be one of: {', '.join(video_fields)}", 400)
    try:
        session = get_session(session_id)
        object_id = session.get(field)
        if not object_id:
            return _error(f"Session has no {field} set", 404)
        result = request_download_url(object_id)
        return jsonify({"download_url": result["downloadUrl"], "expires_in": result["expiresIn"]})
    except ButterbaseError as e:
        return _error(str(e), e.status_code)
