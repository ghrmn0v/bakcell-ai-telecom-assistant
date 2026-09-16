# AI Telecom Assistant

An AI-powered telecom assistant built for a **hackathon**. It reads simulated
telecom datasets (customers, tariffs, packages, transactions) and provides an
AI customer assistant, personalized package recommendations, usage prediction,
issue diagnosis, and a staff copilot.

> **Note:** This is an independent hackathon project. It is **not** an official
> Bakcell product and is not affiliated with or endorsed by Bakcell. The
> datasets are simulated sample data created for the event.

## Features

- **AI Customer Assistant** — Ask questions about your account in natural language
- **Personalized Package Recommendation** — Recommends a tariff based on usage
- **Predictive Usage** — Estimates when data/minutes will run out
- **AI Telecom Doctor** — Diagnoses a described problem and suggests an action
- **Package Comparison** — Side-by-side tariff comparison
- **AI Insight Card** — Proactive insights on the customer dashboard
- **Staff Copilot** — AI-assisted customer support dashboard
- **Graceful AI fallback** — Rule-based responses work without a Gemini API key

## Technologies

- **Backend:** Python, FastAPI, Pandas, Pydantic
- **AI:** Google Gemini API (optional, with a rule-based fallback)
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Data:** CSV datasets (`data/`)

## Project Structure

```
Bakcell_Chatbot_Hackathon/
├── run.py                     # Launcher (starts uvicorn on port 3001)
├── start.sh / start.bat       # Startup scripts
├── data/                      # CSV datasets (customers, tariffs, packages, transactions)
├── backend/
│   ├── main.py                # FastAPI application and routes
│   ├── requirements.txt
│   └── services/
│       ├── data_service.py    # Data loading and analytics
│       └── ai_service.py      # Gemini integration + rule-based fallback
└── frontend/
    ├── index.html             # Customer dashboard
    ├── staff.html             # Staff dashboard
    ├── css/style.css
    └── js/                    # app.js, staff.js, charts.js
```

## Getting Started

### Prerequisites

- Python 3.10–3.12 (the pinned dependency versions may not install on newer
  Python releases)

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

The application runs without a Gemini key: AI features fall back to built-in
rule-based responses when `GEMINI_API_KEY` is not set.

### 3. Run

```bash
python run.py
```

Then open:

- Customer dashboard: `http://localhost:3001`
- Staff dashboard: `http://localhost:3001/staff`

## Environment Variables

| Variable         | Description                                            |
|------------------|--------------------------------------------------------|
| `GEMINI_API_KEY` | Google Gemini API key (optional; fallback is used if unset) |
| `HOST`           | Host to bind (default `0.0.0.0`)                       |
| `PORT`           | Port to bind (default `8000`; `run.py` uses `3001`)    |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/customers` | List customers |
| `GET`  | `/api/customers/{msisdn}` | Customer details |
| `GET`  | `/api/customers/{msisdn}/transactions` | Recent transactions |
| `GET`  | `/api/customers/{msisdn}/usage` | Usage analytics |
| `GET`  | `/api/customers/{msisdn}/recommendation` | Tariff recommendation |
| `GET`  | `/api/customers/{msisdn}/predict` | Usage prediction |
| `GET`  | `/api/customers/{msisdn}/insights` | Account insights |
| `GET`  | `/api/customers/{msisdn}/compare` | Package comparison |
| `GET`  | `/api/tariffs` | List tariffs |
| `GET`  | `/api/packages` | List add-on packages |
| `POST` | `/api/ai/chat` | AI chat (`{ "msisdn", "message" }`) |
| `POST` | `/api/ai/recommend` | AI-assisted recommendation |
| `POST` | `/api/ai/diagnose` | AI issue diagnosis (`{ "msisdn", "problem" }`) |
| `POST` | `/api/support/escalate` | Generate a staff escalation summary |

## What I Learned

- Building a REST API with FastAPI and Pydantic request models
- Structuring an AI feature set around real data with a deterministic fallback
- Working with Pandas for data loading, aggregation, and analytics
- Connecting a vanilla JS + Chart.js frontend to a Python backend
