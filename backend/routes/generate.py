import time
import requests
from flask import Blueprint, request, jsonify
import config
from services.butterbase import update_session, ButterbaseError

generate_bp = Blueprint("generate", __name__)

_BASE = "https://seedanceapi.org/v2"
_POLL_INTERVAL = 5   # seconds between polls
_POLL_TIMEOUT = 300  # 5-minute max wait per request


def _start_job(prompt: str, headers: dict) -> str:
    resp = requests.post(
        f"{_BASE}/generate",
        json={
            "prompt": prompt,
            "duration": 5,
            "aspect_ratio": "16:9",
            "model": "seedance-2.0-fast",
        },
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("code") != 200:
        raise RuntimeError(body.get("message", "unknown error"))
    return body["data"]["task_id"]


def _poll(task_ids: dict, headers: dict) -> dict:
    """
    Poll all task IDs concurrently (single-threaded round-robin) until all
    finish or the timeout is reached.
    task_ids: {"before": "<id>", "after": "<id>"}
    Returns: {"before": "<url>", "after": "<url>"}
    """
    pending = dict(task_ids)
    results = {}
    deadline = time.time() + _POLL_TIMEOUT

    while pending:
        if time.time() > deadline:
            raise TimeoutError(f"Video generation timed out for tasks: {list(pending.keys())}")
        for key, task_id in list(pending.items()):
            resp = requests.get(
                f"{_BASE}/status",
                params={"task_id": task_id},
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            status = data.get("status")
            if status == "SUCCESS":
                results[key] = data["response"][0]
                del pending[key]
            elif status == "FAILED":
                raise RuntimeError(f"Seadance generation failed for '{key}' (task {task_id})")
        if pending:
            time.sleep(_POLL_INTERVAL)

    return results


@generate_bp.post("/")
def generate_video():
    """
    POST /api/generate-video/
    Body: {
      "session_id":             "<string>",  (required — existing Butterbase session to update)
      "correction_description": "<string>",  (required — used as the after-video prompt)
      "movement_type":          "<string>",  (optional — used for the before-video prompt)
      "joint_data":             [...],       (optional — stored in session, not sent to video model)
      "correction_text":        "<string>",  (optional — IonRouter raw correction, stored in session)
    }

    Generates two videos via Seedance:
      - before: generic movement prompt with no correction context
      - after:  conditioned on the verified correction description

    Saves raw_seadance_url, conditioned_seadance_url, joint_data, and correction_text
    back to the Butterbase session, then returns all four fields.
    """
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id")
    correction_description = body.get("correction_description")
    movement_type = body.get("movement_type") or "physical movement exercise"
    joint_data = body.get("joint_data")
    correction_text = body.get("correction_text", correction_description)

    if not session_id or not isinstance(session_id, str):
        return jsonify({"error": "'session_id' must be a non-empty string"}), 400
    if not correction_description or not isinstance(correction_description, str):
        return jsonify({"error": "'correction_description' must be a non-empty string"}), 400

    headers = {
        "Authorization": f"Bearer {config.SEADANCE_API_KEY}",
        "Content-Type": "application/json",
    }

    before_prompt = f"A person performing a {movement_type} with poor form and technique"
    after_prompt = correction_description

    try:
        before_id = _start_job(before_prompt, headers)
        after_id = _start_job(after_prompt, headers)
    except Exception as e:
        return jsonify({"error": f"Failed to start video generation: {e}"}), 502

    try:
        urls = _poll({"before": before_id, "after": after_id}, headers)
    except TimeoutError as e:
        return jsonify({"error": str(e)}), 504
    except Exception as e:
        return jsonify({"error": f"Video generation failed: {e}"}), 502

    session_update = {
        "raw_seadance_url": urls["before"],
        "conditioned_seadance_url": urls["after"],
        "correction_text": correction_text,
    }
    if joint_data is not None:
        session_update["joint_data"] = joint_data

    try:
        update_session(session_id, session_update)
    except ButterbaseError as e:
        # Videos are ready — return them even if the DB write fails
        return jsonify({
            "before_url": urls["before"],
            "after_url": urls["after"],
            "warning": f"Videos generated but session save failed: {e}",
        })

    return jsonify({
        "session_id": session_id,
        "before_url": urls["before"],
        "after_url": urls["after"],
    })
