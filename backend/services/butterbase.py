"""
Thin wrapper around the Butterbase REST API.
All credentials are sourced from config, never hardcoded.
"""
import requests
import config


class ButterbaseError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {config.BUTTERBASE_API_KEY}",
        "Content-Type": "application/json",
    }


def _raise_for(resp: requests.Response):
    if not resp.ok:
        try:
            detail = resp.json().get("error", resp.text)
        except Exception:
            detail = resp.text
        raise ButterbaseError(resp.status_code, detail)


# ---------------------------------------------------------------------------
# Sessions table
# ---------------------------------------------------------------------------

def list_sessions(phone_number: str | None = None, limit: int = 50, offset: int = 0) -> list:
    params = {"order": "created_at.desc", "limit": limit, "offset": offset}
    if phone_number:
        params["phone_number"] = f"eq.{phone_number}"
    resp = requests.get(
        f"{config.BUTTERBASE_API_URL}/sessions",
        headers=_headers(),
        params=params,
        timeout=10,
    )
    _raise_for(resp)
    return resp.json()


def get_session(session_id: str) -> dict:
    resp = requests.get(
        f"{config.BUTTERBASE_API_URL}/sessions",
        headers=_headers(),
        params={"session_id": f"eq.{session_id}", "limit": 1},
        timeout=10,
    )
    _raise_for(resp)
    rows = resp.json()
    if not rows:
        raise ButterbaseError(404, f"Session '{session_id}' not found")
    return rows[0]


def create_session(data: dict) -> dict:
    allowed = {
        "original_video_url", "raw_seadance_url", "conditioned_seadance_url",
        "joint_data", "correction_text", "verified_correction", "phone_number",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    resp = requests.post(
        f"{config.BUTTERBASE_API_URL}/sessions",
        headers=_headers(),
        json=payload,
        timeout=10,
    )
    _raise_for(resp)
    return resp.json()


def update_session(session_id: str, data: dict) -> dict:
    allowed = {
        "original_video_url", "raw_seadance_url", "conditioned_seadance_url",
        "joint_data", "correction_text", "verified_correction", "phone_number",
    }
    payload = {k: v for k, v in data.items() if k in allowed}
    resp = requests.patch(
        f"{config.BUTTERBASE_API_URL}/sessions",
        headers=_headers(),
        params={"session_id": f"eq.{session_id}"},
        json=payload,
        timeout=10,
    )
    _raise_for(resp)
    return resp.json()


# ---------------------------------------------------------------------------
# File storage (presigned URLs — file bytes never touch Flask)
# ---------------------------------------------------------------------------

def request_upload_url(filename: str, content_type: str, size_bytes: int) -> dict:
    """
    Returns uploadUrl, objectId, objectKey, expiresIn.
    The frontend uses uploadUrl to PUT the file directly to storage.
    Store objectId in the sessions table, not the uploadUrl (it expires).
    """
    resp = requests.post(
        f"{config.BUTTERBASE_STORAGE_URL}/upload",
        headers=_headers(),
        json={"filename": filename, "contentType": content_type, "sizeBytes": size_bytes},
        timeout=10,
    )
    _raise_for(resp)
    return resp.json()


def upload_file_server_side(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Upload a file from the backend directly to Butterbase storage.
    Returns the objectId to persist in the database.
    """
    presigned = request_upload_url(filename, content_type, len(file_bytes))
    put_resp = requests.put(
        presigned["uploadUrl"],
        data=file_bytes,
        headers={"Content-Type": content_type},
        timeout=120,
    )
    if not put_resp.ok:
        raise ButterbaseError(put_resp.status_code, f"Storage PUT failed: {put_resp.text}")
    return presigned["objectId"]


def request_download_url(object_id: str) -> dict:
    """Returns a fresh presigned downloadUrl for a stored file."""
    resp = requests.get(
        f"{config.BUTTERBASE_STORAGE_URL}/download/{object_id}",
        headers=_headers(),
        timeout=10,
    )
    _raise_for(resp)
    return resp.json()
