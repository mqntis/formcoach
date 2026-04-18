import os
import subprocess
from openai import OpenAI
from flask import Blueprint, request, jsonify
import config
from services.butterbase import get_session, ButterbaseError

notify_bp = Blueprint("notify", __name__)

_openai = OpenAI(api_key=config.OPENAI_API_KEY)

_SENDER_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "imessage_sender", "send.mjs"
)


def _summarize_errors(correction_text: str) -> str:
    """Use GPT-4o to produce a 2-sentence plain-English summary of the form errors."""
    resp = _openai.chat.completions.create(
        model="gpt-4o",
        max_tokens=120,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a fitness coach summarizing form feedback for an athlete. "
                    "Write exactly 2 short sentences summarizing the main form errors detected. "
                    "Be specific, encouraging, and plain-English. No lists, no markdown."
                ),
            },
            {"role": "user", "content": correction_text},
        ],
    )
    return resp.choices[0].message.content.strip()


def _send_imessage(phone: str, message: str):
    env = {
        **os.environ,
        "PHOTON_PROJECT_ID": config.PHOTON_PROJECT_ID,
        "PHOTON_SECRET_KEY": config.PHOTON_SECRET_KEY,
        "SEND_PHONE": phone,
        "SEND_MESSAGE": message,
    }
    result = subprocess.run(
        ["node", os.path.abspath(_SENDER_SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "iMessage send failed")


@notify_bp.post("/")
def send_results():
    """
    POST /api/send-results/
    Body: { "session_id": "<string>", "phone_number": "<string>" }

    Retrieves the session from Butterbase, generates a 2-sentence error summary,
    and sends an iMessage with the corrected video URL + summary to the phone number.
    """
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id")
    phone_number = body.get("phone_number")

    if not session_id or not isinstance(session_id, str):
        return jsonify({"error": "'session_id' must be a non-empty string"}), 400
    if not phone_number or not isinstance(phone_number, str):
        return jsonify({"error": "'phone_number' must be a non-empty string"}), 400

    try:
        session = get_session(session_id)
    except ButterbaseError as e:
        return jsonify({"error": f"Failed to retrieve session: {e}"}), e.status_code

    video_url = session.get("conditioned_seadance_url")
    correction_text = session.get("correction_text")

    if not video_url:
        return jsonify({"error": "Session has no conditioned video URL yet"}), 422
    if not correction_text:
        return jsonify({"error": "Session has no correction text yet"}), 422

    try:
        summary = _summarize_errors(correction_text)
    except Exception as e:
        return jsonify({"error": f"Failed to generate summary: {e}"}), 502

    message = (
        f"Here's your FormCoach movement correction video:\n{video_url}\n\n"
        f"{summary}"
    )

    try:
        _send_imessage(phone_number, message)
    except subprocess.TimeoutExpired:
        return jsonify({"error": "iMessage send timed out"}), 504
    except Exception as e:
        return jsonify({"error": f"iMessage send failed: {e}"}), 502

    return jsonify({"sent": True, "phone_number": phone_number, "session_id": session_id})
