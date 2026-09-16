# AI Telecom Assistant — Setup Requirements

## Prerequisites

- **Python 3.11+**
- **pip** (Python package manager)
- **Google Gemini API Key** — Get one at https://aistudio.google.com/apikey

## Quick Start

### 1. Clone and enter the project

```bash
cd ai-telecom-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it

- **macOS/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

### 4. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 5. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=AIzaSy...your_key_here
```

### 6. Run the backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Open the frontend

Open `frontend/index.html` in your browser.  
The frontend communicates with the backend at `http://localhost:8000`.

## Required API Keys

| Service | Key | How to get |
|---|---|---|
| Google Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/apikey |

## Architecture

```
Frontend (HTML/CSS/JS)  →  Backend (FastAPI/Python)  →  Pandas + CSV Data
                                            ↓
                                     Gemini AI API
```

## Notes

- CSV data files must be in the `data/` directory
- The app works without a Gemini key (AI features will use fallback responses)
- No database required — all data comes from CSV files
