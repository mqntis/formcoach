import type { UploadUrlResponse, Session } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error ?? "Request failed");
  }
  return res.json();
}

export async function requestUploadUrl(
  file: File
): Promise<UploadUrlResponse> {
  return post("/api/upload/", {
    filename: file.name,
    content_type: file.type,
    size_bytes: file.size,
  });
}

export async function uploadFileToStorage(
  uploadUrl: string,
  file: File
): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!res.ok) throw new Error("Upload to storage failed");
}

export async function createSession(
  phoneNumber: string,
  objectId: string
): Promise<Session> {
  return post("/api/sessions/", {
    phone_number: phoneNumber,
    original_video_url: objectId,
  });
}
