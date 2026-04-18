import type {
  Session, ExtractResult, Analysis, VerifyResult, GenerateResult,
} from "../types";

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

export async function extractJoints(file: File): Promise<ExtractResult> {
  const form = new FormData();
  form.append("video", file);
  const res = await fetch(`${BASE}/api/extract-joints/`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error ?? "Joint extraction failed");
  }
  return res.json();
}

export async function createSession(
  phoneNumber: string,
  objectId: string,
): Promise<Session> {
  return post("/api/sessions/", {
    phone_number: phoneNumber,
    original_video_url: objectId,
  });
}

export async function analyzeForm(jointData: unknown[]): Promise<Analysis> {
  return post("/api/analyze-form/", { joint_data: jointData });
}

export async function verifyCorrection(
  correctionDescription: string,
): Promise<VerifyResult> {
  return post("/api/verify-correction/", {
    correction_description: correctionDescription,
  });
}

export async function generateVideo(params: {
  session_id: string;
  correction_description: string;
  movement_type: string;
  joint_data: unknown[];
  correction_text: string;
}): Promise<GenerateResult> {
  return post("/api/generate-video/", params);
}

export async function sendResults(
  sessionId: string,
  phoneNumber: string,
): Promise<void> {
  await post("/api/send-results/", {
    session_id: sessionId,
    phone_number: phoneNumber,
  });
}
