import os
import tempfile
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision
from flask import Blueprint, request, jsonify
from services.butterbase import upload_file_server_side, ButterbaseError

joints_bp = Blueprint("joints", __name__)

ALLOWED_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}
MAX_BYTES = 500 * 1024 * 1024  # 500 MB

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "pose_landmarker_lite.task")

# Landmark names in index order (0–32)
_LANDMARK_NAMES = [p.name for p in mp_vision.PoseLandmark]


def _build_landmarker() -> mp_vision.PoseLandmarker:
    base_options = mp_tasks.BaseOptions(model_asset_path=os.path.abspath(_MODEL_PATH))
    options = mp_vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return mp_vision.PoseLandmarker.create_from_options(options)


def _extract_joints(video_path: str) -> list[list[dict] | None]:
    """
    Run MediaPipe PoseLandmarker on every frame.
    Returns one entry per frame: list of 33 landmark dicts, or None if no pose detected.
    Each dict: { landmark, x, y, z, visibility }
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames: list[list[dict] | None] = []
    frame_idx = 0

    with _build_landmarker() as landmarker:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(frame_idx * 1000 / fps)
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            if result.pose_landmarks:
                pose = result.pose_landmarks[0]  # first (and only) detected pose
                frames.append([
                    {
                        "landmark": _LANDMARK_NAMES[i],
                        "x": round(lm.x, 6),
                        "y": round(lm.y, 6),
                        "z": round(lm.z, 6),
                        "visibility": round(lm.visibility, 4),
                    }
                    for i, lm in enumerate(pose)
                ])
            else:
                frames.append(None)

            frame_idx += 1

    cap.release()
    return frames


@joints_bp.post("/")
def extract_joints():
    """
    POST /api/extract-joints/
    Accepts multipart/form-data with a 'video' field.

    Steps:
      1. Run MediaPipe PoseLandmarker on every frame
      2. Upload the video to Butterbase storage
      3. Return { object_id, frame_count, joint_data }

    Store object_id in the sessions.original_video_url (or raw_seadance_url) column.
    joint_data can be stored in sessions.joint_data.
    """
    if "video" not in request.files:
        return jsonify({"error": "Missing 'video' field in multipart form"}), 400

    video_file = request.files["video"]
    content_type = video_file.content_type or "video/mp4"

    if content_type not in ALLOWED_TYPES:
        return jsonify({"error": f"Unsupported video type: {content_type}"}), 400

    file_bytes = video_file.read()
    if len(file_bytes) > MAX_BYTES:
        return jsonify({"error": "File exceeds 500 MB limit"}), 413

    suffix = ".mov" if "quicktime" in content_type else ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        joint_data = _extract_joints(tmp_path)

        object_id = upload_file_server_side(
            file_bytes=file_bytes,
            filename=video_file.filename or f"upload{suffix}",
            content_type=content_type,
        )
    except ButterbaseError as e:
        return jsonify({"error": str(e)}), e.status_code
    except Exception as e:
        return jsonify({"error": f"Processing failed: {e}"}), 500
    finally:
        os.unlink(tmp_path)

    return jsonify({
        "object_id": object_id,
        "frame_count": len(joint_data),
        "joint_data": joint_data,
    })
