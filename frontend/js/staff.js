/* ═══════════════════════════════════════════════════════════════════════════
   Staff Dashboard — AI-Powered Customer Support
   ═══════════════════════════════════════════════════════════════════════════ */

const API = '/api';
let selectedMsisdn = '';

document.addEventListener('DOMContentLoaded', () => {
  loadStaffData();
  setupStaffNavigation();
});

function setupStaffNavigation() {
  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', () => {
      const page = item.dataset.page;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
      document.getElementById(`page-${page}`)?.classList.add('active');
    });
  });
}

async function loadStaffData() {
  try {
    const res = await fetch(`${API}/customers`);
    const customers = await res.json();

    // Stats
    const active = customers.filter(c => c.status === 'aktiv').length;
    const blocked = customers.filter(c => c.status !== 'aktiv').length;
    const avgBalance = customers.reduce((sum, c) => sum + (c.balans_azn || 0), 0) / customers.length;

    document.getElementById('statTotalCustomers').textContent = customers.length;
    document.getElementById('statActiveCustomers').textContent = active;
    document.getElementById('statBlockedCustomers').textContent = blocked;
    document.getElementById('statAvgBalance').textContent = `${avgBalance.toFixed(2)} AZN`;

    // Customer select
    const sel = document.getElementById('staffCustomerSelect');
    sel.innerHTML = customers.map(c =>
      `<option value="${c.msisdn}">${c.ad} ${c.soyad} — ${c.msisdn}</option>`
    ).join('');
    sel.addEventListener('change', (e) => { selectedMsisdn = e.target.value; });

    // Customer table
    const tbody = document.getElementById('staffCustomerTable');
    tbody.innerHTML = customers.map(c => `
      <tr>
        <td>${c.musteri_id}</td>
        <td>${c.ad} ${c.soyad}</td>
        <td>${c.msisdn}</td>
        <td>${c.tarif_adi}</td>
        <td>${c.balans_azn?.toFixed(2)} AZN</td>
        <td><span class="status-badge ${c.status === 'aktiv' ? 'aktiv' : 'bloklu'}">${c.status}</span></td>
        <td><button class="btn btn-sm btn-primary" onclick="analyzeCustomer('${c.msisdn}')">Analyze</button></td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Failed to load staff data:', err);
  }
}

function loadCustomerDetail() {
  const sel = document.getElementById('staffCustomerSelect');
  if (sel.value) {
    analyzeCustomer(sel.value);
  }
}

async function analyzeCustomer(msisdn) {
  selectedMsisdn = msisdn;

  // Navigate to analyse page
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector('.nav-item[data-page="analyse"]')?.classList.add('active');
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
  document.getElementById('page-analyse')?.classList.add('active');

  const container = document.getElementById('analysisResult');
  container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    // Load all customer data in parallel
    const [custRes, usageRes, recRes, predRes, insightRes] = await Promise.all([
      fetch(`${API}/customers/${msisdn}`),
      fetch(`${API}/customers/${msisdn}/usage`),
      fetch(`${API}/customers/${msisdn}/recommendation`),
      fetch(`${API}/customers/${msisdn}/predict`),
      fetch(`${API}/customers/${msisdn}/insights`),
    ]);

    const customer = await custRes.json();
    const usage = await usageRes.json();
    const recommendation = await recRes.json();
    const prediction = await predRes.json();
    const insight = await insightRes.json();

    // Build AI summary via chat endpoint
    const chatRes = await fetch(`${API}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ msisdn, message: 'Generate a brief staff-ready customer profile summary in 3-5 bullet points. Focus on: key behavior, spending patterns, potential issues, and recommended actions.' }),
    });
    const chatData = await chatRes.json();

    const util = usage.tariff_utilization || {};
    const spending = usage.spending || {};

    container.innerHTML = `
      <!-- Customer Profile -->
      <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
          <div class="card-title">Customer Profile</div>
          <span class="status-badge ${customer.status === 'aktiv' ? 'aktiv' : 'bloklu'}">${customer.status}</span>
        </div>
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
          <div class="customer-avatar" style="width:56px;height:56px;font-size:22px;">${(customer.ad || '?')[0]}</div>
          <div>
            <div style="font-size:20px;font-weight:700;">${customer.ad} ${customer.soyad}</div>
            <div style="font-size:13px;color:var(--text-muted);">${customer.msisdn} · FIN: ${customer.fin}</div>
            <div style="font-size:12px;color:var(--text-muted);">Born: ${customer.dogum_tarixi} · Registered: ${customer.qeydiyyat_tarixi}</div>
          </div>
        </div>
        <div class="stats-grid">
          <div style="text-align:center;"><div style="font-size:22px;font-weight:800;">${customer.balans_azn?.toFixed(2)} AZN</div><div style="font-size:11px;color:var(--text-muted);">Balance</div></div>
          <div style="text-align:center;"><div style="font-size:22px;font-weight:800;">${customer.tarif_adi}</div><div style="font-size:11px;color:var(--text-muted);">Current Tariff</div></div>
          <div style="text-align:center;"><div style="font-size:22px;font-weight:800;">${customer.internet_qaliq_gb?.toFixed(1)} GB</div><div style="font-size:11px;color:var(--text-muted);">Data Remaining</div></div>
          <div style="text-align:center;"><div style="font-size:22px;font-weight:800;">${customer.deqiqe_qaliq} min</div><div style="font-size:11px;color:var(--text-muted);">Minutes Left</div></div>
        </div>
      </div>

      <!-- AI Summary -->
      <div class="card" style="margin-bottom:20px;">
        <div class="card-header">
          <div class="card-title">🤖 AI Customer Summary</div>
          <div class="confidence">
            <span class="confidence-dot ${insight.confidence > 70 ? 'high' : 'medium'}"></span>
            Confidence: ${insight.confidence || 50}%
          </div>
        </div>
        <div style="background:var(--bg);border-radius:var(--radius-md);padding:16px;line-height:1.7;">
          ${formatChatText(chatData.response || 'No summary available.')}
        </div>
      </div>

      <!-- Usage + Utilization -->
      <div class="grid-2">
        <div class="card">
          <div class="card-header"><div class="card-title">Usage Utilization</div></div>
          <div style="margin-bottom:12px;">
            ${renderStaffBar('Internet', util.internet_pct || 0)}
            ${renderStaffBar('Minutes', util.minutes_pct || 0)}
            ${renderStaffBar('SMS', util.sms_pct || 0)}
          </div>
          <div style="font-size:12px;color:var(--text-muted);">
            Spending: ${spending.total_spent || 0} AZN total · ${spending.package_spend || 0} AZN on add-ons · ${spending.out_of_package_spend || 0} AZN out-of-package
          </div>
        </div>
        <div class="card">
          <div class="card-header"><div class="card-title">Recommendation</div></div>
          ${recommendation.recommended_tariff?.tarif_id !== recommendation.current_tariff?.tarif_id ? `
            <div style="text-align:center;">
              <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">Recommended Plan</div>
              <div style="font-size:20px;font-weight:700;color:var(--success);">${recommendation.recommended_tariff?.ad}</div>
              <div style="font-size:16px;font-weight:600;">${recommendation.recommended_tariff?.qiymet_azn} AZN</div>
              <div style="margin-top:8px;font-size:12px;color:var(--text-muted);">AI Confidence: ${recommendation.confidence}%</div>
            </div>
          ` : `
            <div style="text-align:center;color:var(--success);">
              <div style="font-size:32px;">✅</div>
              <div style="font-weight:600;">Current plan is optimal</div>
            </div>
          `}
        </div>
      </div>

      <!-- Predictions -->
      <div class="card" style="margin-top:20px;">
        <div class="card-header"><div class="card-title">🔮 AI Predictions</div></div>
        ${(prediction.predictions || []).map(p => `
          <div class="prediction-card ${p.severity}" style="margin-bottom:8px;">
            <span class="prediction-icon">${p.severity === 'critical' ? '🔴' : p.severity === 'high' ? '🟠' : '🔵'}</span>
            <div class="prediction-content">
              <h4>${p.type?.replace(/_/g, ' ')}</h4>
              <p>${p.description}</p>
            </div>
          </div>
        `).join('') || '<p style="color:var(--text-muted);font-size:13px;">No predictions available.</p>'}
      </div>
    `;

  } catch (err) {
    console.error('Analysis error:', err);
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error loading analysis</h3><p>Please try again.</p></div>';
  }
}

function renderStaffBar(label, pct) {
  const color = pct > 90 ? 'red' : pct > 70 ? 'orange' : 'green';
  return `
    <div class="usage-bar-group">
      <div class="usage-bar-label">
        <span>${label}</span>
        <span>${pct.toFixed(0)}%</span>
      </div>
      <div class="usage-bar">
        <div class="usage-bar-fill ${color}" style="width:${Math.min(pct, 100)}%"></div>
      </div>
    </div>
  `;
}

function formatChatText(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}
