import json
import re
from openai import OpenAI
from flask import Blueprint, request, jsonify
import config

analyze_bp = Blueprint("analyze", __name__)

_client = OpenAI(
    api_key=config.IONROUTER_API_KEY,
    base_url="https://api.ionrouter.io/v1",
)

# Sample at most this many evenly-spaced frames to keep the prompt a
# reasonable size regardless of video length.
_MAX_FRAMES = 20

# Only send biomechanically relevant landmarks — omits face/finger detail
# that adds tokens without helping movement analysis.
_KEY_LANDMARKS = {
    "NOSE", "LEFT_SHOULDER", "RIGHT_SHOULDER",
    "LEFT_ELBOW", "RIGHT_ELBOW", "LEFT_WRIST", "RIGHT_WRIST",
    "LEFT_HIP", "RIGHT_HIP",
    "LEFT_KNEE", "RIGHT_KNEE",
    "LEFT_ANKLE", "RIGHT_ANKLE",
    "LEFT_HEEL", "RIGHT_HEEL",
}

_SYSTEM_PROMPT = """\
You are a professional movement coach and biomechanics expert.
You will receive joint coordinate data sampled frame by frame from a video of a person performing a physical movement.
Each frame contains 33 landmarks (MediaPipe Pose): x, y, z coordinates (normalised 0–1) and visibility.

Respond ONLY with a valid JSON object — no markdown, no explanation, no extra text — with exactly these three fields:
{
  "movement_type": "<string: the movement being performed>",
  "errors": [
    "<string: specific form error with joint reference>",
    ...
  ],
  "correction_description": "<string: detailed description of what the corrected movement should look like>"
}"""

_USER_TEMPLATE = """\
These are joint coordinates extracted frame by frame from a person performing a physical movement. \
Identify what movement they are performing, list every form error you can detect with specific joint references, \
and describe exactly what the corrected movement should look like in detail.

Sampled joint data ({n_frames} frames, {n_landmarks} landmarks per frame):
{data}"""


def _sample_frames(joint_data: list, max_frames: int) -> list:
    """
    Return up to max_frames evenly-spaced non-null frames,
    filtered to only the biomechanically relevant landmarks.
    """
    valid = [(i, f) for i, f in enumerate(joint_data) if f is not None]
    if not valid:
        return []
    if len(valid) > max_frames:
        step = len(valid) / max_frames
        valid = [valid[int(i * step)] for i in range(max_frames)]
    return [
        [lm for lm in frame if lm["landmark"] in _KEY_LANDMARKS]
        for _, frame in valid
    ]


def _parse_response(text: str) -> dict:
    """Extract the JSON object from the model response."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?```?", "", text).strip()
    # Try direct parse first
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Fall back: find the first {...} block in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group())
    return {
        "movement_type": str(parsed.get("movement_type", "")),
        "errors": list(parsed.get("errors", [])),
        "correction_description": str(parsed.get("correction_description", "")),
    }


@analyze_bp.post("/")
def analyze_form():
    """
    POST /api/analyze-form/
    Body: { "joint_data": [ [{ landmark, x, y, z, visibility }, ...], null, ... ] }

    Sends sampled joint frames to IonRouter and returns:
    { movement_type, errors, correction_description }
    """
    body = request.get_json(silent=True) or {}
    joint_data = body.get("joint_data")

    if not isinstance(joint_data, list) or len(joint_data) == 0:
        return jsonify({"error": "'joint_data' must be a non-empty array"}), 400

    frames = _sample_frames(joint_data, _MAX_FRAMES)
    if not frames:
        return jsonify({"error": "No frames with detected pose landmarks found in joint_data"}), 422

    user_message = _USER_TEMPLATE.format(
        n_frames=len(frames),
        n_landmarks=len(frames[0]),
        data=json.dumps(frames, separators=(",", ":")),
    )

    try:
        response = _client.chat.completions.create(
            model="gpt-oss-120b",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
    except Exception as e:
        return jsonify({"error": f"IonRouter request failed: {e}"}), 502

    raw = response.choices[0].message.content or ""

    try:
        result = _parse_response(raw)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return jsonify({"error": f"Failed to parse model response: {e}", "raw": raw}), 502

    return jsonify(result)
