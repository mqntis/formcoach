from flask import Blueprint, request, jsonify
from services.butterbase import request_upload_url, ButterbaseError

upload_bp = Blueprint("upload", __name__)

ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/webm", "video/x-matroska",
}
MAX_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


@upload_bp.post("/")
def request_video_upload():
    """
    Request a presigned upload URL for a video file.

    Body: { "filename": "squat.mp4", "content_type": "video/mp4", "size_bytes": 12345678 }
    Response: { "upload_url": "...", "object_id": "...", "expires_in": 300 }

    The client PUTs the file directly to upload_url, then stores object_id
    in the relevant sessions field (original_video_url, raw_seadance_url, etc.).
    """
    data = request.get_json(silent=True) or {}

    filename = data.get("filename", "").strip()
    content_type = data.get("content_type", "").strip()
    size_bytes = data.get("size_bytes")

    if not filename:
        return jsonify({"error": "filename is required"}), 400
    if content_type not in ALLOWED_VIDEO_TYPES:
        return jsonify({"error": f"content_type must be one of: {', '.join(sorted(ALLOWED_VIDEO_TYPES))}"}), 400
    if not isinstance(size_bytes, int) or size_bytes <= 0:
        return jsonify({"error": "size_bytes must be a positive integer"}), 400
    if size_bytes > MAX_SIZE_BYTES:
        return jsonify({"error": f"File exceeds maximum size of {MAX_SIZE_BYTES // (1024*1024)} MB"}), 400

    try:
        result = request_upload_url(filename, content_type, size_bytes)
        return jsonify({
            "upload_url": result["uploadUrl"],
            "object_id": result["objectId"],
            "expires_in": result["expiresIn"],
        })
    except ButterbaseError as e:
        return jsonify({"error": str(e)}), e.status_code
