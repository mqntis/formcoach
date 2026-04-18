import { useState, useRef, useCallback } from "react";
import { requestUploadUrl, uploadFileToStorage, createSession } from "./services/api";
import type { Session } from "./types";
import "./App.css";

type Step = "idle" | "requesting" | "uploading" | "creating" | "done" | "error";

const ACCEPTED = ["video/mp4", "video/quicktime"];
const ACCEPTED_EXT = ".mp4,.mov";

function formatPhone(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 10);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
}

function stepLabel(step: Step): string {
  if (step === "requesting") return "Preparing upload…";
  if (step === "uploading")  return "Uploading video…";
  if (step === "creating")   return "Creating session…";
  return "";
}

export default function App() {
  const [file, setFile]               = useState<File | null>(null);
  const [previewUrl, setPreviewUrl]   = useState<string | null>(null);
  const [phone, setPhone]             = useState("");
  const [step, setStep]               = useState<Step>("idle");
  const [session, setSession]         = useState<Session | null>(null);
  const [errorMsg, setErrorMsg]       = useState<string | null>(null);
  const [dragOver, setDragOver]       = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const loading = step === "requesting" || step === "uploading" || step === "creating";

  function pickFile(f: File) {
    if (!ACCEPTED.includes(f.type)) {
      setErrorMsg("Please upload an MP4 or MOV file.");
      return;
    }
    setErrorMsg(null);
    setSession(null);
    setStep("idle");
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  }

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) pickFile(f);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) pickFile(f);
  }, [previewUrl]);

  async function handleAnalyze() {
    if (!file || !phone) return;
    setErrorMsg(null);
    setSession(null);

    try {
      setStep("requesting");
      const { upload_url, object_id } = await requestUploadUrl(file);

      setStep("uploading");
      await uploadFileToStorage(upload_url, file);

      setStep("creating");
      const created = await createSession(phone.replace(/\D/g, ""), object_id);

      setSession(created);
      setStep("done");
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Something went wrong.");
      setStep("error");
    }
  }

  const phoneDigits = phone.replace(/\D/g, "");
  const canAnalyze = !!file && phoneDigits.length === 10 && !loading;

  return (
    <div className="page">
      <header className="header">
        <div className="logo">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="8" fill="var(--accent)" />
            <path d="M8 20 L14 8 L20 20" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M10 16 L18 16" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
          <span className="logo-text">FormCoach</span>
        </div>
        <span className="badge">Beta</span>
      </header>

      <main className="main">
        <div className="hero">
          <h1>Analyze your form,<br />instantly.</h1>
          <p className="subtitle">Upload a video of your movement and get AI-powered coaching feedback.</p>
        </div>

        <div className="card">
          {/* Video upload zone */}
          <div
            className={`drop-zone ${file ? "has-file" : ""} ${dragOver ? "drag-over" : ""}`}
            onClick={() => !file && inputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_EXT}
              onChange={onInputChange}
              style={{ display: "none" }}
            />

            {previewUrl && file ? (
              <div className="preview-wrapper">
                <video
                  className="preview-video"
                  src={previewUrl}
                  controls
                  playsInline
                />
                <button
                  className="change-btn"
                  onClick={e => { e.stopPropagation(); inputRef.current?.click(); }}
                  disabled={loading}
                >
                  Change video
                </button>
              </div>
            ) : (
              <div className="drop-prompt">
                <div className="upload-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <p className="drop-title">Drop your video here</p>
                <p className="drop-sub">or <span className="link">browse files</span></p>
                <p className="drop-hint">MP4 or MOV · max 500 MB</p>
              </div>
            )}
          </div>

          {/* Phone input */}
          <div className="field">
            <label className="field-label" htmlFor="phone">Phone number</label>
            <div className="input-wrapper">
              <span className="input-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.77 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 8.91a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                </svg>
              </span>
              <input
                id="phone"
                className="input"
                type="tel"
                placeholder="(555) 000-0000"
                value={phone}
                onChange={e => setPhone(formatPhone(e.target.value))}
                maxLength={14}
                disabled={loading}
              />
            </div>
          </div>

          {/* Error */}
          {errorMsg && (
            <div className="alert alert-error">{errorMsg}</div>
          )}

          {/* Success */}
          {step === "done" && session && (
            <div className="alert alert-success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Session created — ID: <code>{session.session_id.slice(0, 8)}…</code>
            </div>
          )}

          {/* Analyze button */}
          <button
            className={`analyze-btn ${loading ? "loading" : ""}`}
            onClick={handleAnalyze}
            disabled={!canAnalyze}
          >
            {loading ? (
              <>
                <span className="spinner" />
                {stepLabel(step)}
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Analyze
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
