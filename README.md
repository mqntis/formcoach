# FormCoach

AI-powered form coaching application.

## Project Structure

```
formcoach/
├── backend/          # Python Flask API
│   ├── app.py        # Application factory
│   ├── routes/       # API blueprints
│   ├── models/       # SQLAlchemy models
│   ├── services/     # Business logic
│   └── tests/        # Pytest tests
├── frontend/         # React + TypeScript (Vite)
│   └── src/
│       ├── pages/    # Route-level components
│       ├── context/  # React context (auth, etc.)
│       ├── services/ # API client
│       └── types/    # TypeScript interfaces
├── .env.example      # Required env vars (root)
└── .gitignore
```

## Setup

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in your values
flask run
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # fill in VITE_API_URL
npm run dev
```

## Environment Variables

See `.env.example` (root) and `frontend/.env.example` for all required keys.
