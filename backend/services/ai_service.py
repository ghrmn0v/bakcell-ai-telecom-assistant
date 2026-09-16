"""
AI Service — Gemini API integration for conversational AI, diagnosis,
recommendations, and natural language understanding.
All factual data comes from data_service; Gemini handles language and reasoning.
"""

import os
import json
from typing import Optional

try:
    import google.generativeai as genai
    _HAS_GEMINI = True
except ImportError:
    _HAS_GEMINI = False
    print('[ai_service] google-generativeai not fully installed. AI features will use fallback.')

# Configure Gemini
_api_key = os.getenv("GEMINI_API_KEY", "")
_model = None
if _api_key and _HAS_GEMINI:
    try:
        genai.configure(api_key=_api_key)
        _model = genai.GenerativeModel("gemini-2.0-flash-lite")
    except Exception as e:
        print(f"[ai_service] Failed to configure Gemini: {e}")
else:
    print("[ai_service] No GEMINI_API_KEY or gemini not installed. AI features will use fallback.")

# System prompt for all interactions
_SYSTEM_PROMPT = """You are an AI-powered telecom assistant for a mobile operator (Bakcell-style).
You speak the customer's language. Be concise, helpful, and professional.

CRITICAL RULES:
1. ONLY use the customer data provided in the context. NEVER invent numbers, names, prices, or facts.
2. If you don't have enough information, say so clearly.
3. Always ground your responses in the actual data provided.
4. Use the customer's actual tariff name, balance, usage, and transaction history.
5. Be empathetic when the customer has issues.
6. Format responses clearly with bullet points where helpful.
7. Respond in the same language the customer uses (Azerbaijani or English).
"""


def _call_gemini(prompt: str, context: str = "", customer_ctx: dict = None) -> str:
    """Call Gemini with smart fallback handling."""
    if not _model:
        return _fallback_chat(prompt, customer_ctx or {})

    try:
        full_prompt = f"{_SYSTEM_PROMPT}\n\n{context}\n\nCustomer message: {prompt}"
        response = _model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"[ai_service] Gemini error: {e}")
        return _fallback_chat(prompt, customer_ctx or {})


def _usage_bar(pct: float, width: int = 10) -> str:
    """Create a text-based usage progress bar."""
    filled = int(pct / 100 * width)
    empty = width - filled
    if pct > 90:
        return f"[{'█' * filled}{'░' * empty}]"
    elif pct > 70:
        return f"[{'█' * filled}{'░' * empty}]"
    else:
        return f"[{'█' * filled}{'░' * empty}]"


def _fallback_chat(prompt: str, ctx: dict) -> str:
    """Smart conversational AI when Gemini is unavailable."""
    from services import data_service

    prompt_lower = prompt.lower()
    name = ctx.get('name', 'Customer')
    msisdn = ctx.get('msisdn', '')
    tariff = ctx.get('tariff', {})
    remaining = ctx.get('remaining', {})
    spending = ctx.get('spending', {})
    util = ctx.get('tariff_utilization', {})
    balance = ctx.get('balance', 0)
    recent_tx = ctx.get('recent_transactions', [])

    tariff_name = tariff.get('ad', 'your current plan')
    tariff_price = tariff.get('qiymet_azn', 0)
    internet_gb = tariff.get('internet_gb', 0)
    remaining_gb = remaining.get('internet_gb', 0)
    remaining_min = remaining.get('minutes', 0)
    remaining_sms = remaining.get('sms', 0)
    used_gb = internet_gb - remaining_gb
    used_min = tariff.get('deqiqe', 0) - remaining_min
    used_sms = tariff.get('sms', 0) - remaining_sms
    internet_pct = util.get('internet_pct', 0)
    minutes_pct = util.get('minutes_pct', 0)

    # ── Greetings ──
    if any(w in prompt_lower for w in ['hello', 'hi', 'hey', 'salam', 'salam aleykum', 'salamlar']):
        return (
            f"Hello {name}! 👋 Welcome!\n\n"
            f"I'm your AI telecom assistant. I have full access to your account data and can help you with:\n\n"
            f"📊 **Usage** — " + (f'You have {remaining_gb:.1f} GB data left ({internet_pct:.0f}% used)' if internet_pct > 0 else 'Check your data, minutes, and SMS usage') + f"\n"
            f"💰 **Balance** — Your balance is **{balance:.2f} AZN**\n"
            f"📦 **Recommendations** — Find a better plan for your needs\n"
            f"🔮 **Predictions** — Know when you'll run out\n"
            f"🩺 **Troubleshooting** — Diagnose any telecom issue\n\n"
            f"What would you like to know?"
        )

    # ═══ ORDER MATTERS: Specific handlers FIRST, then general ═══

    # ── Recommendation / Switch questions (BEFORE generic 'plan' match) ──
    if any(w in prompt_lower for w in ['recommend', 'better plan', 'switch plan', 'change plan', 'upgrade', 'which plan', 'what plan', 'downgrade', 'diger paket', 'yaxsi paket']):
        rec = data_service.compute_recommendation(msisdn)
        rec_tariff = rec.get('recommended_tariff', {})
        usage_s = rec.get('usage_summary', {})
        reasons = rec.get('reasons', [])
        confidence = rec.get('confidence', 50)

        if rec_tariff.get('tarif_id') != tariff.get('tarif_id'):
            diff_price = rec_tariff.get('qiymet_azn', 0) - tariff_price
            diff_data = rec_tariff.get('internet_gb', 0) - internet_gb
            price_str = f"+{diff_price:.2f}" if diff_price > 0 else f"{diff_price:.2f}"
            data_str = f"+{diff_data} GB" if diff_data > 0 else f"{diff_data} GB"

            return (
                f"📦 **AI Recommendation** (Confidence: {confidence}%)\n\n"
                f"Your current plan: **{tariff_name}** ({tariff_price} AZN, {internet_gb} GB)\n"
                f"Recommended plan: **{rec_tariff.get('ad', 'N/A')}** ({rec_tariff.get('qiymet_azn', 0)} AZN, {rec_tariff.get('internet_gb', 0)} GB)\n\n"
                f"**Why this plan?**\n"
                + '\n'.join(f"  ✅ {r}" for r in reasons[:4]) + f"\n\n"
                f"**Your projected monthly usage:**\n"
                f"  📶 Data: ~{usage_s.get('projected_monthly_gb', 0):.1f} GB/month\n"
                f"  📞 Minutes: ~{usage_s.get('projected_monthly_minutes', 0)} min/month\n"
                f"  📦 Add-ons purchased: {usage_s.get('package_addon_purchases', 0)} this period\n\n"
                f"💰 Price difference: **{price_str} AZN** | Data difference: **{data_str}**\n\n"
                f"💡 Switching could give you more value for your money!"
            )
        else:
            return (
                f"✅ **Your current plan is optimal!**\n\n"
                f"**{tariff_name}** ({tariff_price} AZN) is already the best fit for your usage patterns.\n\n"
                f"You're using approximately {used_gb:.1f} GB of your {internet_gb} GB allowance, "
                f"which is a good match. No need to change!"
            )

    # ── Problem / Issue / Slow / Not working (BEFORE generic 'internet' match) ──
    if any(w in prompt_lower for w in ['slow', 'not working', 'problem', 'issue', 'error', 'broken', 'yavas', 'ishlemir', 'work']):
        diagnosis = _fallback_diagnose(prompt, ctx)
        severity_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🔵', 'low': '🟢'}.get(diagnosis.get('severity', ''), '⚪')
        return (
            f"🩺 **AI Diagnosis** (Confidence: {diagnosis.get('confidence', 50)}%)\n\n"
            f"**Issue:** {diagnosis.get('issue_name', 'Unknown')}\n"
            f"**Category:** {diagnosis.get('issue_category', 'other')}\n"
            f"**Severity:** {severity_icon} {diagnosis.get('severity', 'medium')}\n\n"
            f"**Explanation:**\n{diagnosis.get('explanation', 'Unable to determine the issue.')}\n\n"
            f"**Recommended Action:**\n{diagnosis.get('recommended_action', 'Contact support for assistance.')}\n\n"
            + (f"⚠️ If this doesn't resolve your issue, use the **Telecom Doctor** page or click **Contact Support** to escalate." if diagnosis.get('confidence', 50) < 70 else "")
        )

    # ── Prediction questions ──
    if any(w in prompt_lower for w in ['predict', 'forecast', 'run out', 'last', 'when will', 'qac gun', 'nece gun']):
        pred = data_service.compute_prediction(msisdn)
        predictions = pred.get('predictions', [])
        daily = pred.get('daily_usage', {})
        days_left = pred.get('days_left_in_cycle', 0)

        lines = []
        for p in predictions:
            icon = {'critical': '🔴', 'high': '🟠', 'medium': '🔵', 'low': '🟢'}.get(p.get('severity', ''), '⚪')
            lines.append(f"  {icon} {p.get('description', '')}")

        return (
            f"🔮 **Usage Predictions**\n\n"
            f"📅 Days remaining in cycle: **{days_left}**\n"
            f"📶 Daily data usage: **{daily.get('internet_gb', 0):.3f} GB/day**\n"
            f"📞 Daily minute usage: **{daily.get('minutes', 0):.1f} min/day**\n\n"
            + ('\n'.join(lines) if lines else f"  ✅ No concerns — your usage is sustainable.")
            + f"\n\n💡 Check the **Predictions** page for detailed charts!"
        )

    # ── Package / Tariff questions (generic — AFTER specific handlers) ──
    if any(w in prompt_lower for w in ['package', 'plan', 'tariff', 'paket', 'tarif', 'current', 'am i on', 'what do i have']):
        features = []
        if internet_gb > 0: features.append(f"\n  📶 **{internet_gb} GB** internet data")
        if tariff.get('deqiqe', 0) > 0: features.append(f"  📞 **{tariff.get('deqiqe', 0)} minutes** of calls")
        if tariff.get('sms', 0) > 0: features.append(f"  ✉️ **{tariff.get('sms', 0)} SMS** messages")
        if tariff.get('sosial_media_gb', 0) > 0: features.append(f"  📱 **{tariff['sosial_media_gb']} GB** social media")
        if str(tariff.get('whatsapp_pulsuz', '')).lower() == 'true': features.append("  💬 **Free WhatsApp**")
        features_str = '\n'.join(features)

        usage_summary = []
        if internet_gb > 0:
            bar = _usage_bar(internet_pct)
            usage_summary.append(f"  📶 {bar} {internet_pct:.0f}% — **{remaining_gb:.1f} GB** left")
        if tariff.get('deqiqe', 0) > 0:
            bar = _usage_bar(minutes_pct)
            usage_summary.append(f"  📞 {bar} {minutes_pct:.0f}% — **{remaining_min}** min left")
        usage_str = '\n'.join(usage_summary)

        return (
            f"📋 **Your Current Plan: {tariff_name}**\n"
            f"💰 **Price:** {tariff_price} AZN / {tariff.get('muddet_gun', 28)} days\n\n"
            f"**What's included:**\n{features_str}\n\n"
            f"**Usage Status:**\n{usage_str}\n\n"
            f"💡 Tip: Ask me to check if there's a better plan for you!"
        )

    # ── Balance questions ──
    if any(w in prompt_lower for w in ['balance', 'money', 'balans', 'azn', 'credit', 'pul', 'nece qaldi']):
        status = '✅ Healthy' if balance > 10 else ('⚠️ Low' if balance > 2 else '🔴 Critical')
        return (
            f"💰 **Account Balance**\n\n"
            f"Current balance: **{balance:.2f} AZN** {status}\n\n"
            f"**This Period:**\n"
            f"  📈 Total top-ups: **{spending.get('total_topped_up', 0):.2f} AZN**\n"
            f"  📉 Total spending: **{spending.get('total_spent', 0):.2f} AZN**\n"
            f"  📦 Add-on purchases: **{spending.get('package_spend', 0):.2f} AZN**\n"
            f"  ⚠️ Out-of-package charges: **{spending.get('out_of_package_spend', 0):.2f} AZN**\n\n"
            f"💡 Keep an eye on out-of-package charges — they add up quickly!"
        )

    # ── Usage / Data questions (generic — AFTER diagnose handler) ──
    if any(w in prompt_lower for w in ['usage', 'data', 'internet', 'used', 'how much', 'ne qeder', 'istifade']):
        return (
            f"📊 **Usage Summary for {tariff_name}**\n\n"
            f"📶 **Internet:** {used_gb:.1f} GB used / {internet_gb} GB total\n"
            f"  {_usage_bar(internet_pct)} {internet_pct:.0f}% — **{remaining_gb:.1f} GB remaining**\n\n"
            f"📞 **Minutes:** {used_min} used / {tariff.get('deqiqe', 0)} total\n"
            f"  {_usage_bar(minutes_pct)} {minutes_pct:.0f}% — **{remaining_min} min remaining**\n\n"
            f"✉️ **SMS:** {used_sms} used / {tariff.get('sms', 0)} total\n"
            f"  **{remaining_sms}** remaining\n\n"
            f"📦 Add-ons purchased: **{spending.get('package_count', 0)}** (costing {spending.get('package_spend', 0):.2f} AZN)\n\n"
            + (f"⚠️ **Warning:** Your data is getting low ({internet_pct:.0f}% used). Consider topping up!" if internet_pct > 75 else f"✅ Your usage looks healthy.")
        )

    # ── Spending / Cost questions ──
    if any(w in prompt_lower for w in ['spend', 'cost', 'pay', 'payment', 'xerc', 'odenis', 'price', 'qiymet', 'how much did i spend']):
        total_addon = spending.get('package_spend', 0)
        oop = spending.get('out_of_package_spend', 0)
        return (
            f"💰 **Spending Breakdown**\n\n"
            f"  📋 Plan subscription: **{tariff_price} AZN**\n"
            f"  📦 Add-on packages: **{total_addon:.2f} AZN** ({spending.get('package_count', 0)} purchases)\n"
            f"  ⚠️ Out-of-package: **{oop:.2f} AZN**\n"
            f"  ──────────────────\n"
            f"  💳 **Total spent:** **{spending.get('total_spent', 0):.2f} AZN**\n"
            f"  📈 **Top-ups:** {spending.get('total_topped_up', 0):.2f} AZN\n\n"
            + (f"💡 **Tip:** You're spending {oop:.2f} AZN on out-of-package services. A higher-tier plan could save you money!" if oop > 1 else f"✅ Your spending looks reasonable for your plan.")
        )

    # ── Add-on / Extra / Buy ──
    if any(w in prompt_lower for w in ['add', 'extra', 'buy', 'purchase', 'elave', 'top up', 'topup', 'artir']):
        pkg_count = spending.get('package_count', 0)
        pkg_spend = spending.get('package_spend', 0)
        return (
            f"📦 **Add-on Packages**\n\n"
            f"You've purchased **{pkg_count}** add-on packages this period, totaling **{pkg_spend:.2f} AZN**.\n\n"
            f"**Available add-on packages:**\n"
            f"  • Daily 300 MB — 0.80 AZN\n"
            f"  • Daily 1 GB — 1.50 AZN\n"
            f"  • Monthly 1.5 GB — 6.00 AZN\n"
            f"  • Monthly 6 GB — 12.00 AZN\n"
            f"  • Monthly 15 GB — 19.00 AZN\n"
            f"  • Monthly 30 GB — 29.00 AZN\n"
            f"  • Unlimited Night (00:00-08:00) — 2.00 AZN\n\n"
            + (f"💡 **Tip:** You're spending {pkg_spend:.2f} AZN on add-ons. A higher-tier plan like **GO 19.99** (15 GB for 19.99 AZN) might be more cost-effective!" if pkg_spend > 15 else f"Your add-on usage is moderate. If you need more data regularly, ask me for a plan recommendation!")
        )

    # ── Transactions / History ──
    if any(w in prompt_lower for w in ['transaction', 'history', 'recent', 'tranzaksiya', 'son']):
        if not recent_tx:
            return f"📋 **No recent transactions** found for your account."
        tx_lines = []
        for tx in recent_tx[:8]:
            amount = tx.get('mebleg_azn', 0)
            icon = '📈' if amount > 0 else '📉'
            sign = '+' if amount > 0 else ''
            desc = tx.get('tesvir', 'Transaction')[:60]
            date = tx.get('tarix', '--')
            tx_lines.append(f"  {icon} {date} — {desc} ({sign}{amount:.2f} AZN)")
        return (
            f"📋 **Recent Transactions**\n\n"
            + '\n'.join(tx_lines) + f"\n\n"
            f"💡 View the full **Transactions** page for all history."
        )

    # ── All plans / Available plans ──
    if any(w in prompt_lower for w in ['all plans', 'all packages', 'available', 'what plans', 'butun tarifler', ' OPTIONS']):
        tariffs = data_service.list_tariffs()
        plan_lines = []
        for t in tariffs:
            marker = ' ← **YOU**' if t.get('tarif_id') == tariff.get('tarif_id') else ''
            plan_lines.append(f"  {'➡️' if t.get('tarif_id') == tariff.get('tarif_id') else '•'} **{t['ad']}** — {t['qiymet_azn']} AZN | {t['internet_gb']} GB | {t['deqiqe']} min | {t['sms']} SMS")
        return (
            f"📋 **All Available Plans**\n\n"
            + '\n'.join(plan_lines) + f"\n\n"
            f"You are currently on: **{tariff_name}**\n"
            f"Ask me to recommend a plan based on your usage!"
        )

    # ── Staff / Support ──
    if any(w in prompt_lower for w in ['support', 'staff', 'agent', 'call', 'help me', 'telefonda']):
        return (
            f"📞 **Need Human Support?**\n\n"
            f"I've analyzed your account ({tariff_name}, {balance:.2f} AZN balance, {remaining_gb:.1f} GB data remaining).\n\n"
            f"Before escalating, let me try to help:\n"
            f"  • Describe your issue in detail — I can diagnose it\n"
            f"  • Check the **Telecom Doctor** page for automated diagnosis\n"
            f"  • Use the **Contact Support** button to get AI-generated escalation summary\n\n"
            f"What specific problem are you experiencing?"
        )

    # ── Thank you ──
    if any(w in prompt_lower for w in ['thank', 'thanks', 'sagol', 'sag ol', 'sag']):
        return f"You're welcome, {name}! 😊 I'm always here to help. Feel free to ask anything about your account!"

    # ── Who are you ──
    if any(w in prompt_lower for w in ['who are you', 'what are you', 'nece ne']):
        return (
            f"I'm your **AI Telecom Assistant** 🤖\n\n"
            f"I have full access to your account data including your plan, balance, usage, transactions, and spending patterns.\n\n"
            f"I can help you:\n"
            f"  📊 Understand your usage\n"
            f"  💰 Track your spending\n"
            f"  📦 Find better plans\n"
            f"  🔮 Predict when you'll run out\n"
            f"  🩺 Diagnose telecom issues\n"
            f"  📞 Escalate to human support\n\n"
            f"What can I help you with?"
        )

    # ── Default (smart catch-all) ──
    # Try to give a helpful overview based on account state
    insights = []
    if internet_pct > 80:
        insights.append(f"⚠️ Your data is **{internet_pct:.0f}% used** — you may run low soon")
    if spending.get('out_of_package_spend', 0) > 2:
        insights.append(f"💰 You've spent **{spending['out_of_package_spend']:.2f} AZN** on out-of-package charges")
    if spending.get('package_count', 0) > 3:
        insights.append(f"📦 You've bought **{spending['package_count']} add-ons** — a higher plan may save money")
    if balance < 5:
        insights.append(f"🔴 Your balance is low at **{balance:.2f} AZN**")

    return (
        f"I understand, {name}. Let me help!\n\n"
        f"**Your Account at a Glance:**\n"
        f"  📋 Plan: **{tariff_name}** ({tariff_price} AZN)\n"
        f"  💰 Balance: **{balance:.2f} AZN**\n"
        f"  📶 Data: **{remaining_gb:.1f} GB** remaining ({internet_pct:.0f}% used)\n"
        f"  📞 Minutes: **{remaining_min}** remaining\n"
        + ('\n\n**AI Insights:**\n' + '\n'.join(f'  {i}' for i in insights) if insights else '')
        + f"\n\n**Try asking me:**\n"
        f"  • \"What's my balance?\"\n"
        f"  • \"How much data have I used?\"\n"
        f"  • \"Recommend a better plan\"\n"
        f"  • \"When will I run out of data?\"\n"
        f"  • \"Why am I being charged extra?\"\n"
        f"  • \"My internet is slow\"\n"
        f"  • \"Show my recent transactions\""
    )


def _fallback_diagnose(problem: str, ctx: dict) -> dict:
    """Rule-based telecom diagnosis without Gemini."""
    problem_lower = problem.lower()
    remaining = ctx.get('remaining', {})
    tariff = ctx.get('tariff', {})
    spending = ctx.get('spending', {})
    utilization = ctx.get('tariff_utilization', {})

    remaining_gb = remaining.get('internet_gb', 0)
    internet_pct = utilization.get('internet_pct', 0)
    balance = ctx.get('balance', 0)

    # Data-related issues
    if any(w in problem_lower for w in ['internet', 'data', 'slow', 'yavas', 'net', 'wifi']):
        if internet_pct > 80:
            severity = 'high' if internet_pct > 90 else 'medium'
            return {
                'issue_category': 'data',
                'issue_name': 'Data Usage Near Limit',
                'severity': severity,
                'confidence': 85,
                'explanation': f'Your data usage is at {internet_pct:.0f}% ({remaining_gb:.1f} GB remaining). High usage can cause slowdowns as you approach your limit.',
                'recommended_action': f'Consider upgrading to a higher-data plan like GO 19.99 (15 GB) or purchasing an add-on package.'
            }
        else:
            return {
                'issue_category': 'network',
                'issue_name': 'Network Quality',
                'severity': 'low',
                'confidence': 60,
                'explanation': f'Your data usage is normal ({internet_pct:.0f}% used). The issue may be related to network coverage in your area rather than your plan.',
                'recommended_action': 'Try restarting your device. If the issue persists, it may be a temporary network issue in your area.'
            }

    # Balance / billing issues
    if any(w in problem_lower for w in ['balance', 'money', 'decreased', 'balans', 'azn', 'pul']):
        oop = spending.get('out_of_package_spend', 0)
        if oop > 1:
            return {
                'issue_category': 'billing',
                'issue_name': 'Out-of-Package Charges',
                'severity': 'medium',
                'confidence': 80,
                'explanation': f'You have been charged {oop:.2f} AZN for out-of-package services (extra SMS, calls outside your plan).',
                'recommended_action': 'Review your usage — consider a plan with more minutes/SMS to avoid extra charges.'
            }
        return {
            'issue_category': 'billing',
            'issue_name': 'Balance Inquiry',
            'severity': 'low',
            'confidence': 65,
            'explanation': f'Your current balance is {balance:.2f} AZN. Charges include plan renewal and any add-on purchases.',
            'recommended_action': 'Check your transaction history for detailed breakdown of charges.'
        }

    # Package not enough
    if any(w in problem_lower for w in ['not enough', 'insufficient', 'limit', 'azmir', 'kifayet']):
        pkg_count = spending.get('package_count', 0)
        if pkg_count > 2:
            return {
                'issue_category': 'tariff',
                'issue_name': 'Plan Mismatch',
                'severity': 'medium',
                'confidence': 82,
                'explanation': f'You have purchased {pkg_count} add-on packages. Your current plan may not meet your needs.',
                'recommended_action': f'Upgrade to a higher-tier plan. I recommend checking available options on the Recommendations page.'
            }
        return {
            'issue_category': 'tariff',
            'issue_name': 'Capacity Concern',
            'severity': 'low',
            'confidence': 60,
            'explanation': 'Your usage is within your current plan limits, but you may benefit from monitoring your usage pattern.',
            'recommended_action': 'Check the Predictions page to see if you are trending toward exceeding your limits.'
        }

    # Minutes
    if any(w in problem_lower for w in ['call', 'minute', 'phone', 'zeng', 'deqiqe']):
        return {
            'issue_category': 'minutes',
            'issue_name': 'Call/Minutes Issue',
            'severity': 'low',
            'confidence': 55,
            'explanation': f'You have {remaining.get("minutes", 0)} minutes remaining on your {tariff.get("ad", "current")} plan.',
            'recommended_action': 'If you need more minutes, consider upgrading to a plan with a higher minute allowance.'
        }

    # Generic
    return {
        'issue_category': 'other',
        'issue_name': 'General Inquiry',
        'severity': 'low',
        'confidence': 50,
        'explanation': f'The issue is not clearly tied to a specific account metric. Your account appears to be in good standing with {remaining_gb:.1f} GB data remaining.',
        'recommended_action': 'If the issue persists, please contact our support team for further assistance.'
    }


# ── Chat (General Assistant) ────────────────────────────────────────────────

def chat(customer_context: dict, user_message: str) -> dict:
    """General AI chat with customer context."""
    context = _build_customer_context(customer_context)
    response = _call_gemini(user_message, context, customer_ctx=customer_context)

    return {
        "response": response,
        "intent": "general_chat",
    }


# ── Package Recommendation (AI-enhanced) ────────────────────────────────────

def recommend(customer_context: dict, data_recommendation: dict) -> dict:
    """AI-enhanced package recommendation with natural language explanation."""
    context = _build_customer_context(customer_context)

    rec = data_recommendation.get("recommended_tariff", {})
    usage = data_recommendation.get("usage_summary", {})

    ai_prompt = f"""Based on the customer's data, provide a personalized package recommendation.

Current tariff: {data_recommendation.get('current_tariff', {}).get('ad', 'Unknown')}
Recommended tariff: {rec.get('ad', 'Unknown')} at {rec.get('qiymet_azn', 0)} AZN
Usage summary: {json.dumps(usage, indent=2)}
Recommendation reasons: {data_recommendation.get('reasons', [])}

Explain in 2-3 sentences:
1. Why the current plan isn't optimal
2. Why the recommended plan is better
3. What the customer will gain

Be specific with numbers from the data. Do NOT invent any information."""

    response = _call_gemini(ai_prompt, context)

    return {
        "response": response,
        "recommendation": data_recommendation,
        "confidence": data_recommendation.get("confidence", 50),
    }


# ── Telecom Doctor (Diagnosis) ──────────────────────────────────────────────

def diagnose(customer_context: dict, problem_description: str, usage_data: dict) -> dict:
    """AI-powered telecom issue diagnosis."""
    context = _build_customer_context(customer_context)

    # Build usage summary for AI
    usage_summary = json.dumps({
        "remaining": usage_data.get("remaining", {}),
        "tariff_utilization": usage_data.get("tariff_utilization", {}),
        "spending": usage_data.get("spending", {}),
        "tariff": usage_data.get("tariff", {}),
    }, indent=2)

    ai_prompt = f"""A customer is reporting a telecom problem. Analyze their data and diagnose the issue.

CUSTOMER PROBLEM: "{problem_description}"

CUSTOMER DATA SUMMARY:
{usage_summary}

Respond in JSON format with these fields:
{{
    "issue_category": "data|minutes|sms|billing|tariff|network|other",
    "issue_name": "short name for the issue",
    "severity": "low|medium|high|critical",
    "confidence": 85,
    "explanation": "2-3 sentence explanation grounded in the actual data",
    "recommended_action": "Specific next step using actual tariff/package names from the data"
}}

Important: Only mention tariff names, prices, and data amounts that are in the customer's actual data."""

    if not _model:
        result = _fallback_diagnose(problem_description, customer_context)
    else:
        raw = _call_gemini(ai_prompt, context, customer_ctx=customer_context)

        # Try to parse JSON from response
        try:
            cleaned = raw.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            result = json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            result = _fallback_diagnose(problem_description, customer_context)

    return {
        "diagnosis": result,
        "problem": problem_description,
    }


# ── Escalation Summary ──────────────────────────────────────────────────────

def generate_escalation(customer_context: dict, diagnosis: dict) -> dict:
    """Generate a structured escalation summary for staff."""
    context = _build_customer_context(customer_context)

    ai_prompt = f"""Generate a concise escalation summary for a telecom staff member.

DIAGNOSIS: {json.dumps(diagnosis, indent=2)}

Generate a JSON response:
{{
    "customer_summary": "1-2 sentences about the customer",
    "issue_summary": "1-2 sentences about the issue",
    "sentiment": "calm|frustrated|angry|confused",
    "priority": "low|medium|high|urgent",
    "suggested_action": "Specific recommended action for staff",
    "relevant_data_points": ["key data point 1", "key data point 2", "key data point 3"]
}}"""

    raw = _call_gemini(ai_prompt, context)

    try:
        cleaned = raw.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        result = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        result = {
            "customer_summary": "Customer reported an issue.",
            "issue_summary": str(diagnosis),
            "sentiment": "frustrated",
            "priority": "medium",
            "suggested_action": "Review customer account and provide assistance.",
            "relevant_data_points": [],
        }

    return result


# ── Context Builder ──────────────────────────────────────────────────────────

def _build_customer_context(data: dict) -> str:
    """Build a compact customer context string for Gemini."""
    parts = []

    # Customer info
    parts.append(f"CUSTOMER: {data.get('name', 'Unknown')} ({data.get('msisdn', 'N/A')})")
    parts.append(f"STATUS: {data.get('status', 'unknown')}")

    # Tariff
    tariff = data.get("tariff", {})
    if tariff:
        parts.append(
            f"CURRENT TARIFF: {tariff.get('ad', 'N/A')} — "
            f"{tariff.get('qiymet_azn', 0)} AZN, "
            f"{tariff.get('internet_gb', 0)} GB internet, "
            f"{tariff.get('deqiqe', 0)} minutes, "
            f"{tariff.get('sms', 0)} SMS, "
            f"{tariff.get('muddet_gun', 0)} days"
        )

    # Remaining
    remaining = data.get("remaining", {})
    if remaining:
        parts.append(
            f"REMAINING: {remaining.get('internet_gb', 0)} GB data, "
            f"{remaining.get('minutes', 0)} min, "
            f"{remaining.get('sms', 0)} SMS"
        )

    # Balance
    parts.append(f"BALANCE: {data.get('balance', 0)} AZN")

    # Recent transactions
    recent_tx = data.get("recent_transactions", [])
    if recent_tx:
        parts.append("RECENT TRANSACTIONS:")
        for tx in recent_tx[:10]:
            parts.append(f"  - {tx.get('tarix', 'N/A')}: {tx.get('tesvir', 'N/A')} ({tx.get('mebleg_azn', 0)} AZN)")

    # Spending
    spending = data.get("spending", {})
    if spending:
        parts.append(
            f"SPENDING: Total {spending.get('total_spent', 0)} AZN spent, "
            f"{spending.get('package_spend', 0)} AZN on add-ons, "
            f"{spending.get('out_of_package_spend', 0)} AZN out-of-package"
        )

    # Utilization
    util = data.get("tariff_utilization", {})
    if util:
        parts.append(
            f"UTILIZATION: Internet {util.get('internet_pct', 0)}%, "
            f"Minutes {util.get('minutes_pct', 0)}%, "
            f"SMS {util.get('sms_pct', 0)}%"
        )

    # Available tariffs
    available = data.get("available_tariffs", [])
    if available:
        parts.append("AVAILABLE TARIFFS:")
        for t in available:
            parts.append(
                f"  - {t.get('ad', 'N/A')}: {t.get('qiymet_azn', 0)} AZN, "
                f"{t.get('internet_gb', 0)} GB, {t.get('deqiqe', 0)} min, "
                f"{t.get('sms', 0)} SMS"
            )

    return "\n".join(parts)
