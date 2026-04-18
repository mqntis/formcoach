<div align="center">

# FormCoach

**AI-powered physical form coaching — upload a movement video and get instant biomechanical feedback, comparison videos, and an iMessage delivered to your phone.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Pose-0097A7?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

</div>

---

## The Problem

Getting quality coaching feedback on physical movement is expensive, inaccessible, and slow. A personal trainer costs $60–$150/hr. Online video reviews take days. Most people train alone with no feedback at all — reinforcing bad habits that lead to injury over time.

FormCoach solves this in under 10 minutes: record yourself, upload the video, and receive a professional-grade biomechanical breakdown plus a side-by-side AI comparison video showing exactly what your movement should look like.

---

## How It Works

```
Video Upload
    │
    ▼
MediaPipe Pose Extraction        — 33 skeletal landmarks extracted frame by frame
    │
    ▼
IonRouter (gpt-oss-120b)         — Movement type identified, form errors listed,
                                   correction description generated
    │
    ▼
OpenAI GPT-4o Verification       — Correction text safety-checked for anatomically
                                   impossible or dangerous advice
    │
    ▼
Seedance Video Generation        — Two 5-second videos generated in parallel:
  ├── "Before" — generic movement prompt, no joint data
  └── "After"  — conditioned on verified correction description
    │
    ▼
Results Page                     — 3-way video comparison + errors + correction
    │
    ▼
Photon Spectrum iMessage         — Results sent directly to user's phone
```

All session data (joint coordinates, correction text, video URLs, phone number) is persisted in **Butterbase** and retrievable via `/api/get-results/:session_id`.

---

## Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| Pose Estimation | [MediaPipe PoseLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) | Extracts 33 skeletal landmarks per frame from the uploaded video |
| AI Movement Analysis | [IonRouter](https://ionrouter.io) | Routes to `gpt-oss-120b` to identify movement type, detect form errors, and generate correction text |
| Correction Verification | [OpenAI GPT-4o](https://platform.openai.com/docs/models/gpt-4o) | Checks correction advice for anatomically impossible claims or dangerous instructions |
| Video Generation | [Seedance](https://seedanceapi.org) | Generates "before" and "after" AI movement videos via ByteDance's text-to-video model |
| iMessage Delivery | [Photon Spectrum](https://photon.codes/spectrum) | Sends the corrected video URL and a 2-sentence error summary to the user's phone via iMessage |
| Database & Storage | [Butterbase](https://butterbase.ai) | Hosts the sessions table and video file storage with presigned URLs |
| Frontend | [React + Vite](https://vitejs.dev/) | Single-page app with drag-and-drop upload, live pipeline status, and 3-way video comparison |
| Backend | [Flask](https://flask.palletsprojects.com/) | REST API with 8 endpoints wiring every service together |

---

## Physical AI — Track 4

FormCoach is built for the **Physical AI** track, which challenges builders to use AI to understand, augment, or improve human physical performance.

Most AI applications operate purely in the digital domain — text in, text out. Physical AI is different: it closes the loop between **what a human body is doing** and **what it should be doing**, using machine perception and generative models as the bridge.

FormCoach embodies this in three concrete ways:

**1. Machine perception of the human body**
MediaPipe extracts 33 biomechanical landmarks (shoulders, hips, knees, ankles, etc.) at every frame. This converts raw pixels into a structured representation of how the body is moving through space — the foundational layer of any physical AI system.

**2. Reasoning over physical movement**
IonRouter's language model interprets the joint coordinate time-series as a biomechanics expert would: identifying the movement type, flagging deviations from correct form (e.g. "knees caving inward at 40° of flexion"), and generating targeted correction instructions. This is AI applied not to words or images, but to the physics of a human body.

**3. Generative demonstration**
Rather than just describing what to fix, FormCoach generates video showing the corrected movement — conditioned on the specific correction derived from the user's own joint data. The gap between "knowing what to fix" and "seeing what it should look like" is one of the hardest parts of self-coached training. Seedance closes that gap.

The result is a full Physical AI loop: **sense → reason → demonstrate → deliver**.

---

## Project Structure

```
formcoach/
├── backend/
│   ├── app.py                  # Flask application factory
│   ├── config.py               # Centralised env var access
│   ├── requirements.txt
│   ├── routes/
│   │   ├── health.py           # GET  /health
│   │   ├── upload.py           # POST /api/upload/
│   │   ├── joints.py           # POST /api/extract-joints/
│   │   ├── analyze.py          # POST /api/analyze-form/
│   │   ├── verify.py           # POST /api/verify-correction/
│   │   ├── generate.py         # POST /api/generate-video/
│   │   ├── sessions.py         # CRUD /api/sessions/ + GET /api/get-results/
│   │   ├── notify.py           # POST /api/send-results/
│   │   └── auth.py             # POST /api/auth/
│   ├── services/
│   │   └── butterbase.py       # Butterbase REST client
│   ├── imessage_sender/
│   │   └── send.mjs            # Node.js Photon Spectrum sender
│   └── models/
│       └── pose_landmarker_lite.task   # MediaPipe model (not in git)
└── frontend/
    └── src/
        ├── App.tsx             # Upload form + results page
        ├── services/api.ts     # Typed API client
        └── types/index.ts      # TypeScript interfaces
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/upload/` | Request a presigned Butterbase upload URL |
| `POST` | `/api/extract-joints/` | Extract MediaPipe landmarks + upload video to Butterbase |
| `POST` | `/api/analyze-form/` | Send joint data to IonRouter for movement analysis |
| `POST` | `/api/verify-correction/` | Verify correction text safety with GPT-4o |
| `POST` | `/api/generate-video/` | Generate before/after videos with Seedance + save session |
| `POST` | `/api/send-results/` | Send iMessage with video URL + summary via Photon |
| `GET` | `/api/get-results/:session_id` | Retrieve full session from Butterbase |
| `GET/POST/PATCH` | `/api/sessions/` | Raw session CRUD |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### 1. Clone

```bash
git clone https://github.com/your-username/formcoach.git
cd formcoach
```

### 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Download the MediaPipe pose model (required — not in git due to file size):

```bash
mkdir -p models
curl -L -o models/pose_landmarker_lite.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
```

Install the iMessage sender dependencies:

```bash
cd imessage_sender && npm install && cd ..
```

### 3. Frontend

```bash
cd ../frontend
npm install
```

### 4. Environment Variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `FLASK_SECRET_KEY` | Any random hex string — `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_SECRET_KEY` | Same as above |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `BUTTERBASE_API_KEY` | [app.butterbase.ai](https://app.butterbase.ai) → Project → API Keys |
| `BUTTERBASE_APP_ID` | Same page |
| `IONROUTER_API_KEY` | [ionrouter.io](https://ionrouter.io) → Dashboard |
| `SEADANCE_API_KEY` | [seedanceapi.org](https://seedanceapi.org) → Dashboard |
| `PHOTON_PROJECT_ID` | [app.photon.codes](https://app.photon.codes) → Project → Settings |
| `PHOTON_SECRET_KEY` | Same page |

Your `.env` should look like:

```env
FLASK_ENV=development
FLASK_SECRET_KEY=your-hex-key
FLASK_DEBUG=1

DATABASE_URL=sqlite:///formcoach.db

JWT_SECRET_KEY=your-hex-key

FRONTEND_URL=http://localhost:3000

OPENAI_API_KEY=sk-proj-...

BUTTERBASE_API_KEY=bb_sk_...
BUTTERBASE_APP_ID=app_...
BUTTERBASE_API_BASE=https://api.butterbase.ai

IONROUTER_API_KEY=sk-...

SEADANCE_API_KEY=...

PHOTON_PROJECT_ID=...
PHOTON_SECRET_KEY=...
```

---

## Running Locally

**Backend** (from `backend/`):

```bash
source venv/bin/activate
python app.py
# Runs on http://localhost:5000
```

**Frontend** (from `frontend/`):

```bash
npm run dev
# Runs on http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173), drop in a workout video, enter your phone number, and click **Analyze**.

---

## Testing the API

```bash
# Health check
curl http://localhost:5000/health

# Verify correction endpoint
curl -s -X POST http://localhost:5000/api/verify-correction/ \
  -H "Content-Type: application/json" \
  -d '{"correction_description": "Keep your back straight and knees tracking over your toes during the squat."}' \
  | python3 -m json.tool

# Retrieve a session
curl http://localhost:5000/api/get-results/<session_id> | python3 -m json.tool
```

---

## Notes

- **Video generation takes 2–5 minutes** — Seedance queues jobs asynchronously. The frontend shows a live status and polls until both videos are ready.
- **iMessage requires Photon Pro** — Cloud mode provisions a shared iMessage relay. Enable iMessage in your Photon dashboard under Platforms before testing.
- **MediaPipe model is not in git** — The `.task` file is ~3 MB and excluded via `.gitignore`. Use the `curl` command above to download it on first setup.
- **Joint data is sampled** — The analyze endpoint samples up to 20 evenly-spaced frames and filters to 15 biomechanically relevant landmarks to stay within the LLM context window.
