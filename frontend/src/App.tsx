import { useState, useRef, useCallback } from "react";
import {
  extractJoints, createSession, analyzeForm,
  verifyCorrection, generateVideo, sendResults,
} from "./services/api";
import type { Session, Analysis } from "./types";
import "./App.css";

type Step =
  | "idle" | "extracting" | "creating" | "analyzing"
  | "verifying" | "generating" | "done" | "error";

type IMessageStatus = "pending" | "sent" | "failed" | null;

const ACCEPTED     = ["video/mp4", "video/quicktime"];
const ACCEPTED_EXT = ".mp4,.mov";

function formatPhone(raw: string): string {
  const d = raw.replace(/\D/g, "").slice(0, 10);
  if (d.length <= 3) return d;
  if (d.length <= 6) return `(${d.slice(0, 3)}) ${d.slice(3)}`;
  return `(${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6)}`;
}

function stepLabel(step: Step): string {
  switch (step) {
    case "extracting": return "Analyzing movement…";
    case "creating":   return "Creating session…";
    case "analyzing":  return "Identifying form errors…";
    case "verifying":  return "Verifying corrections…";
    case "generating": return "Generating comparison videos…";
    default:           return "";
  }
}

function stepSub(step: Step): string {
  if (step === "generating") return "This can take 2–5 minutes";
  return "";
}

const Header = () => (
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
);

export default function App() {
  const [file, setFile]               = useState<File | null>(null);
  const [previewUrl, setPreviewUrl]   = useState<string | null>(null);
  const [phone, setPhone]             = useState("");
  const [step, setStep]               = useState<Step>("idle");
  const [session, setSession]         = useState<Session | null>(null);
  const [analysis, setAnalysis]       = useState<Analysis | null>(null);
  const [beforeUrl, setBeforeUrl]     = useState<string | null>(null);
  const [afterUrl, setAfterUrl]       = useState<string | null>(null);
  const [iMsg, setIMsg]               = useState<IMessageStatus>(null);
  const [errorMsg, setErrorMsg]       = useState<string | null>(null);
  const [dragOver, setDragOver]       = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const loading = step !== "idle" && step !== "done" && step !== "error";

  function reset() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null); setPreviewUrl(null); setPhone("");
    setStep("idle"); setSession(null); setAnalysis(null);
    setBeforeUrl(null); setAfterUrl(null); setIMsg(null);
    setErrorMsg(null);
  }

  function pickFile(f: File) {
    if (!ACCEPTED.includes(f.type)) {
      setErrorMsg("Please upload an MP4 or MOV file.");
      return;
    }
    setErrorMsg(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  }

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
    setAnalysis(null);
    setBeforeUrl(null);
    setAfterUrl(null);
    setIMsg(null);

    const rawPhone  = phone.replace(/\D/g, "");
    const e164Phone = `+1${rawPhone}`;

    try {
      setStep("extracting");
      const { object_id, joint_data } = await extractJoints(file);

      setStep("creating");
      const created = await createSession(rawPhone, object_id);
      setSession(created);

      setStep("analyzing");
      const analysisResult = await analyzeForm(joint_data);
      setAnalysis(analysisResult);

      setStep("verifying");
      const verifyResult = await verifyCorrection(analysisResult.correction_description);

      setStep("generating");
      const { before_url, after_url } = await generateVideo({
        session_id:             created.session_id,
        correction_description: verifyResult.final_correction,
        movement_type:          analysisResult.movement_type,
        joint_data,
        correction_text:        analysisResult.correction_description,
      });
      setBeforeUrl(before_url);
      setAfterUrl(after_url);

      setStep("done");
      setIMsg("pending");
      sendResults(created.session_id, e164Phone)
        .then(() => setIMsg("sent"))
        .catch(() => setIMsg("failed"));

    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : "Something went wrong.");
      setStep("error");
    }
  }

  const phoneDigits = phone.replace(/\D/g, "");
  const canAnalyze  = !!file && phoneDigits.length === 10 && !loading;

  // ── Results page ────────────────────────────────────────────────
  if (step === "done" && session && analysis && beforeUrl && afterUrl) {
    return (
      <div className="page">
        <Header />
        <main className="main results-main">

          {/* iMessage banner */}
          {iMsg === "pending" && (
            <div className="imsg-banner imsg-pending">
              <span className="spinner spinner-sm" />
              Sending to your phone…
            </div>
          )}
          {iMsg === "sent" && (
            <div className="imsg-banner imsg-sent">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              Sent to your phone!
            </div>
          )}
          {iMsg === "failed" && (
            <div className="imsg-banner imsg-failed">
              iMessage delivery failed — check your phone number and try again.
            </div>
          )}

          {/* Video grid */}
          <div className="video-grid">
            {[
              { label: "Your Movement",          src: previewUrl! },
              { label: "AI Without Joint Data",  src: beforeUrl },
              { label: "AI With Joint Data",     src: afterUrl },
            ].map(({ label, src }) => (
              <div className="video-card" key={label}>
                <span className="video-label">{label}</span>
                <video
                  className="result-video"
                  src={src}
                  controls
                  playsInline
                  muted
                />
              </div>
            ))}
          </div>

          {/* Analysis info */}
          <div className="info-card">
            <div className="info-section">
              <span className="info-eyebrow">Movement detected</span>
              <p className="movement-type">{analysis.movement_type}</p>
            </div>

            {analysis.errors.length > 0 && (
              <div className="info-section">
                <span className="info-eyebrow">Form errors detected</span>
                <ul className="error-list">
                  {analysis.errors.map((err, i) => (
                    <li className="error-item" key={i}>
                      <span className="error-dot" />
                      {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="info-section">
              <span className="info-eyebrow">Correction</span>
              <p className="correction-text">{analysis.correction_description}</p>
            </div>
          </div>

          <button className="reset-btn" onClick={reset}>
            Analyze another video
          </button>
        </main>
      </div>
    );
  }

  // ── Upload page ──────────────────────────────────────────────────
  return (
    <div className="page">
      <Header />
      <main className="main">
        <div className="hero">
          <h1>Analyze your form,<br />instantly.</h1>
          <p className="subtitle">Upload a video of your movement and get AI-powered coaching feedback.</p>
        </div>

        <div className="card">
          {/* Drop zone */}
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
              onChange={e => { const f = e.target.files?.[0]; if (f) pickFile(f); }}
              style={{ display: "none" }}
            />
            {previewUrl && file ? (
              <div className="preview-wrapper">
                <video className="preview-video" src={previewUrl} controls playsInline />
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

          {/* Phone */}
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

          {errorMsg && <div className="alert alert-error">{errorMsg}</div>}

          {/* Loading status */}
          {loading && (
            <div className="loading-status">
              <div className="loading-row">
                <span className="spinner" />
                <span className="loading-label">{stepLabel(step)}</span>
              </div>
              {stepSub(step) && <p className="loading-sub">{stepSub(step)}</p>}
            </div>
          )}

          <button
            className={`analyze-btn ${loading ? "loading" : ""}`}
            onClick={handleAnalyze}
            disabled={!canAnalyze}
          >
            {loading ? "Working…" : (
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
