import json
import re
from openai import OpenAI
from flask import Blueprint, request, jsonify
import config

verify_bp = Blueprint("verify", __name__)

_client = OpenAI(api_key=config.OPENAI_API_KEY)

_SYSTEM_PROMPT = (
    "You are a physical movement and biomechanics expert. "
    "Review the following form correction advice and check for any anatomically impossible claims, "
    "dangerous recommendations, or hallucinated instructions. "
    "If the advice is safe and accurate return it as-is. "
    "If anything is wrong, fix it and return the corrected version. "
    "Always return JSON with fields: verified (true/false), issues_found (array), final_correction (string)."
)


def _parse_response(text: str) -> dict:
    text = re.sub(r"```(?:json)?```?", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group())
    return {
        "verified": bool(parsed.get("verified", False)),
        "issues_found": list(parsed.get("issues_found", [])),
        "final_correction": str(parsed.get("final_correction", "")),
    }


@verify_bp.post("/")
def verify_correction():
    """
    POST /api/verify-correction/
    Body: { "correction_description": "<string>" }

    Sends correction text to GPT-4o for biomechanical safety review.
    Returns: { verified, issues_found, final_correction }
    """
    body = request.get_json(silent=True) or {}
    correction_description = body.get("correction_description")

    if not correction_description or not isinstance(correction_description, str):
        return jsonify({"error": "'correction_description' must be a non-empty string"}), 400

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            temperature=0.2,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": correction_description},
            ],
        )
    except Exception as e:
        return jsonify({"error": f"OpenAI request failed: {e}"}), 502

    raw = response.choices[0].message.content or ""

    try:
        result = _parse_response(raw)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return jsonify({"error": f"Failed to parse model response: {e}", "raw": raw}), 502

    return jsonify(result)
