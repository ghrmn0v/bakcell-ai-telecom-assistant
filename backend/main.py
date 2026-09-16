"""
AI Telecom Assistant — FastAPI Backend
All routes for customer data, AI features, and staff dashboard.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from typing import Optional

# Load .env from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from services import data_service, ai_service

app = FastAPI(title="AI Telecom Assistant", version="1.0.0")

# CORS — allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    data_service.load_all()


# ── Request Models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    msisdn: str
    message: str

    @field_validator('msisdn', mode='before')
    @classmethod
    def coerce_msisdn(cls, v):
        return str(v)

class DiagnoseRequest(BaseModel):
    msisdn: str
    problem: str

    @field_validator('msisdn', mode='before')
    @classmethod
    def coerce_msisdn(cls, v):
        return str(v)

class EscalateRequest(BaseModel):
    msisdn: str
    diagnosis: dict

    @field_validator('msisdn', mode='before')
    @classmethod
    def coerce_msisdn(cls, v):
        return str(v)


# ── Helper: Build full customer context for AI ───────────────────────────────

def _clean_nan(obj):
    """Recursively replace NaN/None values for JSON serialization."""
    import math
    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_nan(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def _build_context(msisdn: str) -> dict:
    """Build a full customer context dict for AI services."""
    cust = data_service.get_customer(msisdn)
    if not cust:
        return None

    usage = data_service.get_usage_analytics(msisdn)
    transactions = data_service.get_transactions(msisdn, limit=10)
    tariffs = data_service.list_tariffs()

    return {
        "msisdn": msisdn,
        "name": f"{cust.get('ad', '')} {cust.get('soyad', '')}",
        "status": cust.get("status", "unknown"),
        "balance": cust.get("balans_azn", 0),
        "tariff": usage.get("tariff", {}),
        "remaining": usage.get("remaining", {}),
        "spending": usage.get("spending", {}),
        "tariff_utilization": usage.get("tariff_utilization", {}),
        "recent_transactions": transactions,
        "available_tariffs": tariffs,
    }


# ── Customer Endpoints ───────────────────────────────────────────────────────

@app.get("/api/customers")
def api_list_customers():
    return _clean_nan(data_service.list_customers())


@app.get("/api/customers/{msisdn}")
def api_get_customer(msisdn: str):
    cust = data_service.get_customer(msisdn)
    if not cust:
        raise HTTPException(404, "Customer not found")
    # Add tariff details
    tariff = data_service.get_tariff(cust["tarif_id"])
    cust["tariff_details"] = tariff
    return _clean_nan(cust)


@app.get("/api/customers/{msisdn}/transactions")
def api_get_transactions(msisdn: str, limit: int = 50):
    cust = data_service.get_customer(msisdn)
    if not cust:
        raise HTTPException(404, "Customer not found")
    return _clean_nan(data_service.get_transactions(msisdn, limit))


@app.get("/api/customers/{msisdn}/usage")
def api_get_usage(msisdn: str):
    result = data_service.get_usage_analytics(msisdn)
    if not result:
        raise HTTPException(404, "Customer not found")
    return _clean_nan(result)


@app.get("/api/customers/{msisdn}/recommendation")
def api_get_recommendation(msisdn: str):
    result = data_service.compute_recommendation(msisdn)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return _clean_nan(result)


@app.get("/api/customers/{msisdn}/predict")
def api_get_prediction(msisdn: str):
    result = data_service.compute_prediction(msisdn)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return _clean_nan(result)


@app.get("/api/customers/{msisdn}/insights")
def api_get_insights(msisdn: str):
    result = data_service.compute_insight(msisdn)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return _clean_nan(result)


@app.get("/api/customers/{msisdn}/compare")
def api_compare_packages(msisdn: str, target: Optional[str] = None):
    result = data_service.compare_packages(msisdn, target)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return _clean_nan(result)


# ── Tariff & Package Endpoints ──────────────────────────────────────────────

@app.get("/api/tariffs")
def api_list_tariffs():
    return _clean_nan(data_service.list_tariffs())


@app.get("/api/packages")
def api_list_packages():
    return _clean_nan(data_service.list_packages())


# ── AI Endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/ai/chat")
def api_ai_chat(req: ChatRequest):
    ctx = _build_context(req.msisdn)
    if not ctx:
        raise HTTPException(404, "Customer not found")
    return ai_service.chat(ctx, req.message)


@app.post("/api/ai/recommend")
def api_ai_recommend(req: ChatRequest):
    ctx = _build_context(req.msisdn)
    if not ctx:
        raise HTTPException(404, "Customer not found")
    data_rec = data_service.compute_recommendation(req.msisdn)
    return _clean_nan(ai_service.recommend(ctx, data_rec))


@app.post("/api/ai/diagnose")
def api_ai_diagnose(req: DiagnoseRequest):
    ctx = _build_context(req.msisdn)
    if not ctx:
        raise HTTPException(404, "Customer not found")
    usage = data_service.get_usage_analytics(req.msisdn)
    return _clean_nan(ai_service.diagnose(ctx, req.problem, usage))


# ── Escalation Endpoint ──────────────────────────────────────────────────────

@app.post("/api/support/escalate")
def api_escalate(req: EscalateRequest):
    ctx = _build_context(req.msisdn)
    if not ctx:
        raise HTTPException(404, "Customer not found")
    escalation = ai_service.generate_escalation(ctx, req.diagnosis)
    escalation["customer"] = ctx
    escalation["diagnosis"] = req.diagnosis
    return _clean_nan(escalation)


# ── Serve Frontend ───────────────────────────────────────────────────────────

frontend_dir = project_root / "frontend"

@app.get("/")
def serve_index():
    return FileResponse(frontend_dir / "index.html")

@app.get("/staff")
def serve_staff():
    return FileResponse(frontend_dir / "staff.html")


# Mount static files (CSS, JS)
app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")
