"""
Data Service — loads CSV datasets with Pandas and provides all data queries,
analytics, recommendations, and predictions. No AI calls here — pure computation.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

# Resolve data directory — walk up from backend/services/ to project root, then into data/
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")

# ── Global DataFrames (loaded once) ──────────────────────────────────────────
customers_df: Optional[pd.DataFrame] = None
tariffs_df: Optional[pd.DataFrame] = None
packages_df: Optional[pd.DataFrame] = None
transactions_df: Optional[pd.DataFrame] = None


def load_all():
    """Load all CSV files into memory. Call once at startup."""
    global customers_df, tariffs_df, packages_df, transactions_df

    import sys
    sys.stdout.write('[data] Loading customers...\n')
    sys.stdout.flush()
    customers_df = pd.read_csv(os.path.join(_DATA_DIR, "musteriler.csv"), encoding="utf-8-sig")
    sys.stdout.write('[data] Loading tariffs...\n')
    sys.stdout.flush()
    tariffs_df = pd.read_csv(os.path.join(_DATA_DIR, "tarifler.csv"), encoding="utf-8-sig")
    sys.stdout.write('[data] Loading packages...\n')
    sys.stdout.flush()
    packages_df = pd.read_csv(os.path.join(_DATA_DIR, "paketler.csv"), encoding="utf-8-sig")
    sys.stdout.write('[data] Loading transactions...\n')
    sys.stdout.flush()
    transactions_df = pd.read_csv(os.path.join(_DATA_DIR, "tranzaksiyalar.csv"), encoding="utf-8-sig")
    # Dates stay as strings — we parse on-demand with _parse_date / _parse_date_to_sortkey
    print(f"[data_service] Loaded: {len(customers_df)} customers, {len(tariffs_df)} tariffs, "
          f"{len(packages_df)} packages, {len(transactions_df)} transactions")

    sys.stdout.write(f"[data_service] Loaded: {len(customers_df)} customers, {len(tariffs_df)} tariffs, "
          f"{len(packages_df)} packages, {len(transactions_df)} transactions\n")
    sys.stdout.flush()


# ── Customer Lookups ─────────────────────────────────────────────────────────

def get_customer(msisdn: str) -> Optional[dict]:
    """Return full customer profile as dict, or None."""
    # Handle both string and int msisdn
    try:
        msisdn_int = int(msisdn)
    except (ValueError, TypeError):
        msisdn_int = None
    if msisdn_int is not None:
        row = customers_df[customers_df["msisdn"] == msisdn_int]
    else:
        row = customers_df[customers_df["msisdn"] == msisdn]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def get_customer_by_id(musteri_id: str) -> Optional[dict]:
    row = customers_df[customers_df["musteri_id"] == musteri_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def list_customers() -> list[dict]:
    """Return lightweight customer list for selection."""
    cols = ["musteri_id", "msisdn", "ad", "soyad", "tarif_adi", "status", "balans_azn"]
    return customers_df[cols].to_dict(orient="records")


# ── Tariff & Package Lookups ─────────────────────────────────────────────────

def get_tariff(tarif_id: str) -> Optional[dict]:
    row = tariffs_df[tariffs_df["tarif_id"] == tarif_id]
    if row.empty:
        return None
    return row.iloc[0].to_dict()


def list_tariffs() -> list[dict]:
    return tariffs_df.to_dict(orient="records")


def list_packages() -> list[dict]:
    return packages_df.to_dict(orient="records")


# ── Date Helpers ─────────────────────────────────────────────────────────────
from datetime import datetime as _dt

def _parse_date(date_str):
    """Parse DD.MM.YYYY string to datetime. Returns None on failure."""
    if not isinstance(date_str, str):
        return None
    try:
        return _dt.strptime(date_str.strip(), "%d.%m.%Y")
    except (ValueError, AttributeError):
        return None

def _parse_datetime(dt_str):
    """Parse DD.MM.YYYY HH:MM string to datetime. Returns None on failure."""
    if not isinstance(dt_str, str):
        return None
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return _dt.strptime(dt_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None

def _date_to_sort_key(date_val):
    """Convert a date value (string or datetime) to a comparable sort key string (YYYYMMDD)."""
    if isinstance(date_val, _dt):
        return date_val.strftime("%Y%m%d")
    if isinstance(date_val, str):
        return date_val.strip().replace(".", "")[:8]  # DD.MM.YYYY -> YYYYMMDD reversed... no
    return "00000000"

def _parse_date_to_sortkey(date_str):
    """Parse DD.MM.YYYY to YYYYMMDD for comparison."""
    if not isinstance(date_str, str):
        return "00000000"
    parts = date_str.strip().split(".")
    if len(parts) == 3:
        return parts[2] + parts[1] + parts[0]  # YYYYMMDD
    return "00000000"

def _period_transactions(msisdn: str, activation_date_str: str = None) -> pd.DataFrame:
    """Get transactions for the current billing period."""
    import numpy as np
    tx = _customer_transactions(msisdn)
    if not activation_date_str or not isinstance(activation_date_str, str):
        return tx
    start_key = _parse_date_to_sortkey(activation_date_str)
    keys = [_parse_date_to_sortkey(v) for v in tx["tarix"]]
    mask = np.array([k >= start_key for k in keys])
    return tx.loc[mask]


# ── Transaction Queries ──────────────────────────────────────────────────────

def get_transactions(msisdn: str, limit: int = 50) -> list[dict]:
    """Get recent transactions for a customer."""
    tx = transactions_df[transactions_df["msisdn"] == msisdn].copy()
    # Sort by date string (YYYYMMDD format from DD.MM.YYYY HH:MM)
    sort_keys = [_parse_date_to_sortkey(v)[:8] if _parse_date_to_sortkey(v) != '00000000' else '00000000' for v in tx['tarix']]
    tx = tx.assign(_sk=sort_keys).sort_values('_sk', ascending=False).drop('_sk', axis=1).head(limit)
    records = tx.to_dict(orient="records")
    # tarix is already a string — no need to format
    for r in records:
        if not isinstance(r.get("tarix"), str):
            r["tarix"] = None
    return records


def _customer_transactions(msisdn: str) -> pd.DataFrame:
    return transactions_df[transactions_df["msisdn"] == msisdn].copy()


# ── Usage Analytics ──────────────────────────────────────────────────────────

def get_usage_analytics(msisdn: str) -> dict:
    """Compute usage analytics from customer data + transactions."""
    cust = get_customer(msisdn)
    if not cust:
        return {}

    tariff = get_tariff(cust["tarif_id"])
    tx = _customer_transactions(msisdn)

    # Current period stats
    activation_date_str = cust.get("tarif_aktivlesme")
    period_tx = _period_transactions(msisdn, activation_date_str)

    # Spending breakdown
    spending = {}
    if not period_tx.empty:
        by_type = period_tx.groupby("tip")["mebleg_azn"].sum()
        spending = by_type.to_dict()

    total_spent = abs(sum(v for v in spending.values() if v < 0))
    total_topped_up = sum(v for v in spending.values() if v > 0)

    # Package purchases (data add-ons)
    package_purchases = period_tx[period_tx["tip"] == "paket_alisi"]
    package_spend = abs(package_purchases["mebleg_azn"].sum()) if not package_purchases.empty else 0
    package_count = len(package_purchases)

    # Out-of-package charges
    oop_tx = period_tx[period_tx["tip"].str.contains("paketdenkenar", na=False)]
    oop_spend = abs(oop_tx["mebleg_azn"].sum()) if not oop_tx.empty else 0

    # Daily spending trend (last 30 days)
    recent_tx = tx[tx["tarix"] >= datetime.now() - timedelta(days=30)]
    daily_spend = {}
    if not recent_tx.empty:
        daily_groups = recent_tx.groupby(recent_tx["tarix"].dt.date)["mebleg_azn"].sum()
        daily_spend = {str(k): round(float(v), 2) for k, v in daily_groups.items()}

    # Transaction type distribution
    tx_type_dist = {}
    if not period_tx.empty:
        tx_type_dist = period_tx["tip"].value_counts().to_dict()

    # Channel distribution
    channel_dist = {}
    if not period_tx.empty:
        channel_dist = period_tx["kanal"].value_counts().to_dict()

    # Tariff utilization
    utilization = {}
    if tariff:
        internet_gb = tariff.get("internet_gb", 0)
        deqiqe = tariff.get("deqiqe", 0)
        sms = tariff.get("sms", 0)
        remaining_internet = cust.get("internet_qaliq_gb", 0)
        remaining_min = cust.get("deqiqe_qaliq", 0)
        remaining_sms = cust.get("sms_qaliq", 0)

        if internet_gb > 0:
            utilization["internet_pct"] = round((1 - remaining_internet / internet_gb) * 100, 1)
        if deqiqe > 0:
            utilization["minutes_pct"] = round((1 - remaining_min / deqiqe) * 100, 1)
        if sms > 0:
            utilization["sms_pct"] = round((1 - remaining_sms / sms) * 100, 1)

    return {
        "msisdn": msisdn,
        "balance": cust.get("balans_azn", 0),
        "remaining": {
            "internet_gb": cust.get("internet_qaliq_gb", 0),
            "minutes": cust.get("deqiqe_qaliq", 0),
            "sms": cust.get("sms_qaliq", 0),
            "social_media_gb": cust.get("sosial_media_qaliq_gb", 0),
            "ai_gb": cust.get("ai_qaliq_gb", 0),
        },
        "tariff": tariff,
        "tariff_utilization": utilization,
        "spending": {
            "total_spent": round(total_spent, 2),
            "total_topped_up": round(total_topped_up, 2),
            "package_spend": round(package_spend, 2),
            "package_count": int(package_count),
            "out_of_package_spend": round(oop_spend, 2),
        },
        "spending_breakdown": {k: round(float(v), 2) for k, v in spending.items()},
        "daily_spend": daily_spend,
        "transaction_type_distribution": tx_type_dist,
        "channel_distribution": channel_dist,
    }


# ── Package Recommendation ───────────────────────────────────────────────────

def compute_recommendation(msisdn: str) -> dict:
    """Compute the best tariff recommendation using deterministic logic."""
    cust = get_customer(msisdn)
    if not cust:
        return {"error": "Customer not found"}

    current_tariff = get_tariff(cust["tarif_id"])
    if not current_tariff:
        return {"error": "Tariff not found"}

    # Compute actual usage from remaining + allocated
    internet_used_gb = current_tariff.get("internet_gb", 0) - cust.get("internet_qaliq_gb", 0)
    minutes_used = current_tariff.get("deqiqe", 0) - cust.get("deqiqe_qaliq", 0)
    sms_used = current_tariff.get("sms", 0) - cust.get("sms_qaliq", 0)

    # Estimate billing period progress
    activation_str = cust.get("tarif_aktivlesme")
    expiry_str = cust.get("tarif_bitme")
    activation_dt = _parse_date(activation_str) if isinstance(activation_str, str) else None
    expiry_dt = _parse_date(expiry_str) if isinstance(expiry_str, str) else None
    if activation_dt and expiry_dt:
        total_days = (expiry_dt - activation_dt).days
        days_passed = (_dt.now() - activation_dt).days
        period_pct = min(days_passed / max(total_days, 1), 1.0)
    else:
        total_days = 28
        period_pct = 0.5
        days_passed = 14

    # Projected monthly usage
    if period_pct > 0.1:
        projected_internet = internet_used_gb / period_pct
        projected_minutes = minutes_used / period_pct
        projected_sms = sms_used / period_pct
    else:
        projected_internet = internet_used_gb
        projected_minutes = minutes_used
        projected_sms = sms_used

    # Count out-of-package spending
    activation_date_str = cust.get("tarif_aktivlesme")
    period_tx = _period_transactions(msisdn, activation_date_str)

    extra_call_min = 0
    oop_tx = period_tx[period_tx["tip"].str.contains("paketdenkenar_zeng", na=False)]
    if not oop_tx.empty:
        extra_call_min = oop_tx.shape[0] * 5  # approximate 5 min per out-of-package call

    extra_sms = 0
    oop_sms = period_tx[period_tx["tip"].str.contains("paketdenkenar_sms", na=False)]
    if not oop_sms.empty:
        extra_sms = oop_sms.shape[0] * 3  # approximate 3 SMS per out-of-package SMS

    # Package add-on purchases indicate data shortfall
    pkg_tx = period_tx[period_tx["tip"] == "paket_alisi"]
    pkg_purchases = len(pkg_tx)

    # Evaluate each tariff — personalized scoring
    all_tariffs = tariffs_df.to_dict(orient="records")
    scores = []
    for t in all_tariffs:
        score = 0
        reasons = []
        t_internet = t["internet_gb"]
        t_minutes = t["deqiqe"]
        t_sms = t["sms"]
        t_price = t["qiymet_azn"]

        # ═══ INTERNET FIT (most important — 40 points max) ═══
        if projected_internet > t_internet:
            shortfall_pct = (projected_internet - t_internet) / max(projected_internet, 0.1) * 100
            score -= shortfall_pct * 0.5  # penalty proportional to shortfall
            reasons.append(f"Needs {projected_internet:.1f} GB but plan has only {t_internet} GB")
        else:
            utilization = projected_internet / max(t_internet, 0.1) * 100
            if utilization >= 60 and utilization <= 95:
                score += 30  # excellent fit — plan is well-utilized
                reasons.append(f"Excellent data fit ({utilization:.0f}% utilization)")
            elif utilization >= 40:
                score += 15  # decent fit
                reasons.append(f"Good data fit ({utilization:.0f}% utilization)")
            elif utilization >= 20:
                score += 0  # oversized but not terrible
                reasons.append(f"Plan has more data than needed ({utilization:.0f}% utilization)")
            else:
                score -= 20  # way too much waste
                reasons.append(f"Plan is oversized ({utilization:.0f}% utilization — paying for unused data)")

        # ═══ MINUTES FIT (15 points max) ═══
        total_minutes_needed = projected_minutes + extra_call_min
        if total_minutes_needed > t_minutes:
            score -= 20
            reasons.append(f"Not enough minutes ({total_minutes_needed:.0f} needed vs {t_minutes} included)")
        else:
            min_util = total_minutes_needed / max(t_minutes, 1) * 100
            if min_util >= 30:
                score += 15  # good minutes fit
            elif min_util >= 10:
                score += 5   # okay
            # No penalty for excess minutes — they're cheap

        # ═══ SMS FIT (5 points max) ═══
        total_sms_needed = projected_sms + extra_sms
        if total_sms_needed > t_sms:
            score -= 10
            reasons.append(f"Not enough SMS ({total_sms_needed:.0f} needed vs {t_sms} included)")
        else:
            score += 5

        # ═══ PRICE EFFICIENCY (20 points max) ═══
        # Calculate cost efficiency: how much value per AZN
        if t_internet >= projected_internet and total_minutes_needed <= t_minutes:
            # This plan covers the needs — score by cost
            # Lower price = higher score, but penalize plans that are too cheap (might not cover needs)
            value_score = (t_internet * 3 + t_minutes * 0.05 + t_sms * 0.1) / max(t_price, 0.1)
            score += min(20, value_score * 2)  # cap at 20
        elif t_price < current_tariff.get('qiymet_azn', 0):
            # Cheaper plan but doesn't fully cover needs
            score += 5  # small bonus for lower cost
            reasons.append("Lower cost but may not cover all needs")

        # ═══ ADD-ON BONUS (15 points max) ═══
        # If customer buys many add-ons, a higher plan saves money
        if pkg_purchases > 1:
            total_addon_spend = abs(pkg_tx["mebleg_azn"].sum())
            current_total = current_tariff.get('qiymet_azn', 0) + total_addon_spend
            if t_price <= current_total and t_internet >= projected_internet:
                score += 15
                reasons.append(f"Could save {current_total - t_price:.2f} AZN vs current plan + add-ons")

        # ═══ CURRENT PLAN DISCOUNT ═══
        if t["tarif_id"] == cust["tarif_id"]:
            score -= 5  # prefer recommending a change

        # ═══ BONUS: social media fit ═══
        if cust.get("sosial_media_qaliq_gb", 0) > 0 and t.get("sosial_media_gb", 0) > 0:
            score += 5

        # ═══ BONUS: WhatsApp free ═══
        if str(t.get('whatsapp_pulsuz', '')).lower() == 'true' and internet_used_gb > current_tariff.get('internet_gb', 0) * 0.5:
            score += 3  # useful for heavy data users

        scores.append({
            "tarif": t,
            "score": round(score, 1),
            "reasons": reasons,
        })

    scores.sort(key=lambda x: x["score"], reverse=True)
    best = scores[0]

    # Find current in scores
    current_score = next((s for s in scores if s["tarif"]["tarif_id"] == cust["tarif_id"]), None)

    # Build recommendation
    is_current_best = best["tarif"]["tarif_id"] == cust["tarif_id"]
    recommended = best if not is_current_best else (scores[1] if len(scores) > 1 else best)

    confidence = min(max(recommended["score"] / 50 * 100, 30), 99) if recommended["score"] > 0 else 40

    return {
        "current_tariff": current_tariff,
        "recommended_tariff": recommended["tarif"],
        "confidence": round(confidence),
        "reasons": recommended["reasons"],
        "usage_summary": {
            "internet_used_gb": round(internet_used_gb, 2),
            "projected_monthly_gb": round(projected_internet, 2),
            "minutes_used": int(minutes_used),
            "projected_monthly_minutes": int(projected_minutes),
            "sms_used": int(sms_used),
            "extra_call_minutes": int(extra_call_min),
            "extra_sms": int(extra_sms),
            "package_addon_purchases": pkg_purchases,
            "period_pct_used": round(period_pct * 100, 1),
        },
        "all_scores": [{"tarif_id": s["tarif"]["tarif_id"], "score": s["score"]} for s in scores],
    }


# ── Predictive Usage ─────────────────────────────────────────────────────────

def compute_prediction(msisdn: str) -> dict:
    """Predict data exhaustion, spending, etc."""
    cust = get_customer(msisdn)
    if not cust:
        return {"error": "Customer not found"}

    tariff = get_tariff(cust["tarif_id"])
    if not tariff:
        return {"error": "Tariff not found"}

    remaining_internet = cust.get("internet_qaliq_gb", 0)
    remaining_minutes = cust.get("deqiqe_qaliq", 0)
    remaining_sms = cust.get("sms_qaliq", 0)
    balance = cust.get("balans_azn", 0)

    activation_str = cust.get("tarif_aktivlesme")
    expiry_str = cust.get("tarif_bitme")
    activation_dt = _parse_date(activation_str) if isinstance(activation_str, str) else None
    expiry_dt = _parse_date(expiry_str) if isinstance(expiry_str, str) else None

    # Days remaining in billing cycle
    if expiry_dt:
        days_left = max((expiry_dt - _dt.now()).days, 0)
    else:
        days_left = 14

    if activation_dt:
        days_elapsed = max((_dt.now() - activation_dt).days, 1)
    else:
        days_elapsed = 14

    total_days = days_left + days_elapsed

    # Daily usage rates
    internet_used = tariff.get("internet_gb", 0) - remaining_internet
    minutes_used = tariff.get("deqiqe", 0) - remaining_minutes
    sms_used = tariff.get("sms", 0) - remaining_sms

    daily_internet = internet_used / max(days_elapsed, 1)
    daily_minutes = minutes_used / max(days_elapsed, 1)
    daily_sms = sms_used / max(days_elapsed, 1)

    # Predictions
    predictions = []

    # Internet exhaustion
    if daily_internet > 0 and remaining_internet > 0:
        days_until_empty = remaining_internet / daily_internet
        if days_until_empty <= days_left:
            date_empty = datetime.now() + timedelta(days=days_until_empty)
            predictions.append({
                "type": "internet_exhaustion",
                "severity": "high" if days_until_empty < 2 else "medium",
                "days_remaining": round(days_until_empty, 1),
                "expected_date": date_empty.strftime("%d.%m.%Y"),
                "daily_usage_gb": round(daily_internet, 2),
                "remaining_gb": round(remaining_internet, 2),
                "description": f"At your current rate ({daily_internet:.2f} GB/day), your data will run out in approximately {days_until_empty:.0f} days ({date_empty.strftime('%d.%m.%Y')}).",
            })
        else:
            predictions.append({
                "type": "internet_sufficient",
                "severity": "low",
                "days_remaining": round(days_until_empty, 1),
                "daily_usage_gb": round(daily_internet, 2),
                "remaining_gb": round(remaining_internet, 2),
                "description": f"Your data should last the billing cycle. You have {remaining_internet:.1f} GB remaining with {days_left} days left.",
            })
    elif remaining_internet <= 0:
        predictions.append({
            "type": "internet_depleted",
            "severity": "critical",
            "description": "You have no internet data remaining.",
        })

    # Minutes exhaustion
    if daily_minutes > 0 and remaining_minutes > 0:
        days_until_empty = remaining_minutes / daily_minutes
        if days_until_empty <= days_left:
            predictions.append({
                "type": "minutes_exhaustion",
                "severity": "high" if days_until_empty < 3 else "medium",
                "days_remaining": round(days_until_empty, 1),
                "daily_usage": round(daily_minutes, 1),
                "remaining": remaining_minutes,
                "description": f"You may run out of minutes in ~{days_until_empty:.0f} days.",
            })

    # Balance prediction (spending rate)
    tx = _customer_transactions(msisdn)
    if not tx.empty:
        topups = tx[tx["tip"] == "balans_artirma"]
        charges = tx[tx["mebleg_azn"] < 0]
        if not charges.empty:
            # Last 30 days spending
            recent = charges[charges["tarix"] >= datetime.now() - timedelta(days=30)]
            recent_spend = abs(recent["mebleg_azn"].sum()) if not recent.empty else 0
            daily_spend = recent_spend / 30
            if daily_spend > 0:
                days_until_zero = balance / daily_spend
                if days_until_zero < days_left:
                    predictions.append({
                        "type": "balance_depletion",
                        "severity": "high" if days_until_zero < 3 else "medium",
                        "days_remaining": round(days_until_zero, 1),
                        "daily_spend": round(daily_spend, 2),
                        "current_balance": balance,
                        "description": f"At your spending rate ({daily_spend:.2f} AZN/day), your balance may run low in ~{days_until_zero:.0f} days.",
                    })

    # Package add-on trend
    pkg_tx = tx[tx["tip"] == "paket_alisi"]
    if len(pkg_tx) > 3:
        predictions.append({
            "type": "addon_trend",
            "severity": "medium",
            "purchase_count": len(pkg_tx),
            "total_spend": round(abs(pkg_tx["mebleg_azn"].sum()), 2),
            "description": f"You've purchased {len(pkg_tx)} add-on packages totaling {abs(pkg_tx['mebleg_azn'].sum()):.2f} AZN. A higher-tier tariff may be more cost-effective.",
        })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    predictions.sort(key=lambda x: severity_order.get(x["severity"], 99))

    return {
        "msisdn": msisdn,
        "days_left_in_cycle": days_left,
        "daily_usage": {
            "internet_gb": round(daily_internet, 3),
            "minutes": round(daily_minutes, 1),
            "sms": round(daily_sms, 1),
        },
        "predictions": predictions,
    }


# ── AI Insight Card ──────────────────────────────────────────────────────────

def compute_insight(msisdn: str) -> dict:
    """Generate a concise AI insight from data."""
    usage = get_usage_analytics(msisdn)
    prediction = compute_prediction(msisdn)
    recommendation = compute_recommendation(msisdn)

    if not usage or "error" in usage:
        return {"error": "Could not compute insight"}

    # Determine primary insight
    insights = []
    alerts = []

    # Data usage insight
    util = usage.get("tariff_utilization", {})
    internet_pct = util.get("internet_pct", 0)
    if internet_pct > 90:
        insights.append(f"⚠️ You've used {internet_pct:.0f}% of your data allowance.")
        alerts.append("high")
    elif internet_pct > 70:
        insights.append(f"📊 You've used {internet_pct:.0f}% of your data — usage is elevated.")

    # Predictions
    for p in prediction.get("predictions", []):
        if p["severity"] in ("critical", "high"):
            insights.append(p["description"])
            alerts.append(p["severity"])

    # Spending insight
    spending = usage.get("spending", {})
    if spending.get("out_of_package_spend", 0) > 2:
        insights.append(f"💰 You've spent {spending['out_of_package_spend']:.2f} AZN on out-of-package services.")
    if spending.get("package_count", 0) > 2:
        insights.append(f"📦 You've purchased {spending['package_count']} add-on packages.")

    # Recommendation insight
    if recommendation.get("recommended_tariff") and recommendation["recommended_tariff"]["tarif_id"] != usage["tariff"]["tarif_id"]:
        rec = recommendation["recommended_tariff"]
        insights.append(f"💡 We recommend {rec['ad']} ({rec['qiymet_azn']} AZN) for better value.")

    # Combine into a primary insight
    primary = insights[0] if insights else "✅ Your account looks good. Your current plan matches your usage well."
    max_severity = "high" if "critical" in alerts or "high" in alerts else ("medium" if alerts else "low")

    return {
        "msisdn": msisdn,
        "primary_insight": primary,
        "all_insights": insights,
        "severity": max_severity,
        "confidence": recommendation.get("confidence", 50),
    }


# ── Package Comparison ───────────────────────────────────────────────────────

def compare_packages(msisdn: str, target_tarif_id: str = None) -> dict:
    """Compare current package against recommended or specific alternative."""
    cust = get_customer(msisdn)
    if not cust:
        return {"error": "Customer not found"}

    current = get_tariff(cust["tarif_id"])
    if target_tarif_id:
        target = get_tariff(target_tarif_id)
    else:
        rec = compute_recommendation(msisdn)
        target = rec.get("recommended_tariff")

    if not current or not target:
        return {"error": "Tariff not found"}

    # Compute differences
    internet_diff = target["internet_gb"] - current["internet_gb"]
    minutes_diff = target["deqiqe"] - current["deqiqe"]
    sms_diff = target["sms"] - current["sms"]
    price_diff = target["qiymet_azn"] - current["qiymet_azn"]

    return {
        "current": current,
        "target": target,
        "differences": {
            "internet_gb": internet_diff,
            "minutes": minutes_diff,
            "sms": sms_diff,
            "price_azn": price_diff,
        },
        "recommendation_reasons": compute_recommendation(msisdn).get("reasons", []),
    }
