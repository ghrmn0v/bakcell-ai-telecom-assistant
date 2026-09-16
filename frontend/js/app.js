/* ═══════════════════════════════════════════════════════════════════════════
   AI Telecom Assistant — Customer Dashboard Logic
   ═══════════════════════════════════════════════════════════════════════════ */

const API = '/api';
let currentMsisdn = '';
let currentPage = 'overview';

// ── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  await loadCustomerList();
  setupNavigation();
  setupChatEnter();
});

// ── Navigation ──────────────────────────────────────────────────────────────
function setupNavigation() {
  document.querySelectorAll('.nav-item[data-page]').forEach(item => {
    item.addEventListener('click', () => {
      const page = item.dataset.page;
      navigateTo(page);
    });
  });
}

function navigateTo(page) {
  currentPage = page;
  // Update nav
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');
  // Show page
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
  document.getElementById(`page-${page}`)?.classList.add('active');
  // Load page-specific data
  if (currentMsisdn) {
    loadPageData(page);
  }
}

async function loadPageData(page) {
  switch (page) {
    case 'overview': await loadOverview(); break;
    case 'insights': await loadInsights(); break;
    case 'recommendation': await loadRecommendation(); break;
    case 'predictions': await loadPredictions(); break;
    case 'comparison': await loadComparison(); break;
    case 'transactions': await loadTransactions(); break;
    case 'chat': initChat(); break;
  }
}

function initChat() {
  const container = document.getElementById('chatMessages');
  if (container && container.children.length === 0) {
    addChatMessage(
      `Hello! 👋 I'm your AI telecom assistant. I have full access to your account data.\n\n` +
      `I can help you with:\n` +
      `📊 Usage analysis\n` +
      `💰 Balance & spending\n` +
      `📦 Plan recommendations\n` +
      `🔮 Usage predictions\n` +
      `🩺 Issue diagnosis\n` +
      `📋 Transaction history\n\n` +
      `Use the quick buttons below or type your question!`
    );
  }
  // Show quick actions
  const qa = document.getElementById('quickActions');
  if (qa) qa.style.display = 'flex';
  // Focus the input
  setTimeout(() => {
    document.getElementById('chatInput')?.focus();
  }, 100);
}

// ── Customer List ───────────────────────────────────────────────────────────
async function loadCustomerList() {
  try {
    const res = await fetch(`${API}/customers`);
    const customers = await res.json();
    const sel = document.getElementById('customerSelect');
    sel.innerHTML = customers.map(c =>
      `<option value="${c.msisdn}">${c.ad} ${c.soyad} — ${c.msisdn}</option>`
    ).join('');
    // Select first active customer
    const firstActive = customers.find(c => c.status === 'aktiv');
    if (firstActive) {
      sel.value = firstActive.msisdn;
      selectCustomer(firstActive.msisdn);
    }
    sel.addEventListener('change', (e) => selectCustomer(e.target.value));
  } catch (err) {
    console.error('Failed to load customers:', err);
  }
}

async function selectCustomer(msisdn) {
  currentMsisdn = msisdn;
  await loadOverview();
  loadPageData(currentPage);
}

// ── Overview ────────────────────────────────────────────────────────────────
async function loadOverview() {
  if (!currentMsisdn) return;

  try {
    // Load multiple things in parallel
    const [custRes, usageRes, insightRes, predRes] = await Promise.all([
      fetch(`${API}/customers/${currentMsisdn}`),
      fetch(`${API}/customers/${currentMsisdn}/usage`),
      fetch(`${API}/customers/${currentMsisdn}/insights`),
      fetch(`${API}/customers/${currentMsisdn}/predict`),
    ]);

    const customer = await custRes.json();
    const usage = await usageRes.json();
    const insight = await insightRes.json();
    const prediction = await predRes.json();

    // Header
    document.getElementById('headerAvatar').textContent = (customer.ad || '?')[0];
    document.getElementById('headerName').textContent = `${customer.ad} ${customer.soyad}`;
    document.getElementById('headerPhone').textContent = customer.msisdn;

    const statusEl = document.getElementById('headerStatus');
    statusEl.textContent = customer.status === 'aktiv' ? 'Active' : customer.status;
    statusEl.className = `status-badge ${customer.status === 'aktiv' ? 'aktiv' : 'bloklu'}`;

    // Stats
    document.getElementById('statBalance').textContent = `${customer.balans_azn?.toFixed(2) || '0.00'}`;
    document.getElementById('statInternet').textContent = `${customer.internet_qaliq_gb?.toFixed(1) || '0'}`;
    document.getElementById('statMinutes').textContent = customer.deqiqe_qaliq || '0';
    document.getElementById('statSms').textContent = customer.sms_qaliq || '0';

    // AI Insight Hero
    const insightHeroEl = document.getElementById('insightHero');
    insightHeroEl.querySelector('.insight-text').textContent = insight.primary_insight || 'Loading...';
    const conf = insight.confidence || 0;
    insightHeroEl.querySelector('.insight-sub').textContent = `AI Confidence: ${conf}%`;

    // Current Plan
    const td = customer.tariff_details;
    if (td) {
      document.getElementById('planName').textContent = td.ad;
      document.getElementById('planPrice').innerHTML = `${td.qiymet_azn} <span>AZN / ${td.muddet_gun} days</span>`;
      const features = document.getElementById('planFeatures');
      features.innerHTML = `
        <li><span>Data</span> <strong>${td.internet_gb} GB</strong></li>
        <li><span>Minutes</span> <strong>${td.deqiqe} min</strong></li>
        <li><span>SMS</span> <strong>${td.sms}</strong></li>
        <li><span>Social Media</span> <strong>${td.sosial_media_gb || 0} GB</strong></li>
        <li><span>WhatsApp</span> <strong>${td.whatsapp_pulsuz === 'true' || td.whatsapp_pulsuz === true ? 'Free ✓' : 'No'}</strong></li>
      `;
    }

    // Usage Bars
    renderUsageBars(usage);

    // Predictions Preview
    renderPredictionsPreview(prediction.predictions || []);

    // Spending chart
    renderSpendingChart(usage.daily_spend || {});


  } catch (err) {
    console.error('Failed to load overview:', err);
    showToast('Error loading dashboard data');
  }
}

function renderUsageBars(usage) {
  const container = document.getElementById('usageBars');
  const util = usage.tariff_utilization || {};
  const remaining = usage.remaining || {};

  const bars = [
    { label: 'Internet', pct: util.internet_pct || 0, remaining: `${remaining.internet_gb || 0} GB` },
    { label: 'Minutes', pct: util.minutes_pct || 0, remaining: `${remaining.minutes || 0} min` },
    { label: 'SMS', pct: util.sms_pct || 0, remaining: `${remaining.sms || 0} msgs` },
  ];

  container.innerHTML = bars.map(b => {
    const color = b.pct > 90 ? 'red' : b.pct > 70 ? 'orange' : 'green';
    return `
      <div class="usage-bar-group">
        <div class="usage-bar-label">
          <span>${b.label}</span>
          <span>${b.pct.toFixed(0)}% used — ${b.remaining} left</span>
        </div>
        <div class="usage-bar">
          <div class="usage-bar-fill ${color}" style="width:${Math.min(b.pct, 100)}%"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderPredictionsPreview(predictions) {
  const container = document.getElementById('predictionsPreview');
  if (!predictions.length) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">✅</div><h3>No urgent predictions</h3><p>Your usage looks healthy.</p></div>';
    return;
  }
  container.innerHTML = predictions.slice(0, 3).map(p => {
    const icon = p.severity === 'critical' ? '🔴' : p.severity === 'high' ? '🟠' : p.severity === 'medium' ? '🔵' : '🟢';
    return `
      <div class="prediction-card ${p.severity}">
        <span class="prediction-icon">${icon}</span>
        <div class="prediction-content">
          <h4>${formatPredictionType(p.type)}</h4>
          <p>${p.description}</p>
        </div>
      </div>
    `;
  }).join('');
}

// ── AI Insights Page ────────────────────────────────────────────────────────
async function loadInsights() {
  if (!currentMsisdn) return;
  const res = await fetch(`${API}/customers/${currentMsisdn}/insights`);
  const data = await res.json();

  const heroEl = document.getElementById('insightHeroFull');
  heroEl.innerHTML = `
    <div class="insight-badge">🤖 AI Insight</div>
    <div class="insight-text">${data.primary_insight}</div>
    <div class="insight-sub">AI Confidence: ${data.confidence || 50}% · Severity: ${data.severity || 'low'}</div>
  `;

  const container = document.getElementById('allInsights');
  const insights = data.all_insights || [];
  if (insights.length <= 1) {
    container.innerHTML = '<div class="card"><div class="empty-state"><div class="empty-icon">✅</div><h3>All good!</h3><p>Your account usage is healthy with no major concerns.</p></div></div>';
    return;
  }
  container.innerHTML = insights.slice(1).map(ins => `
    <div class="prediction-card medium" style="margin-bottom:12px;">
      <span class="prediction-icon">💡</span>
      <div class="prediction-content"><p>${ins}</p></div>
    </div>
  `).join('');
}

// ── Recommendation Page ─────────────────────────────────────────────────────
async function loadRecommendation() {
  if (!currentMsisdn) return;
  const container = document.getElementById('recommendationContent');
  container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    const res = await fetch(`${API}/customers/${currentMsisdn}/recommendation`);
    const data = await res.json();

    const current = data.current_tariff;
    const recommended = data.recommended_tariff;
    const usage = data.usage_summary;

    let html = `
      <div class="grid-2" style="margin-bottom:24px;">
        <div class="tariff-card current">
          <div class="tariff-name">${current.ad}</div>
          <div class="tariff-price">${current.qiymet_azn} <span>AZN</span></div>
          <ul class="tariff-features">
            <li><span>Data</span> <strong>${current.internet_gb} GB</strong></li>
            <li><span>Minutes</span> <strong>${current.deqiqe} min</strong></li>
            <li><span>SMS</span> <strong>${current.sms}</strong></li>
            <li><span>Duration</span> <strong>${current.muddet_gun} days</strong></li>
          </ul>
          <div style="margin-top:12px;font-size:12px;color:var(--text-muted);">Current Plan</div>
        </div>

        ${recommended.tarif_id !== current.tarif_id ? `
        <div class="tariff-card recommended">
          <div class="tariff-name">${recommended.ad}</div>
          <div class="tariff-price">${recommended.qiymet_azn} <span>AZN</span></div>
          <ul class="tariff-features">
            <li><span>Data</span> <strong>${recommended.internet_gb} GB</strong></li>
            <li><span>Minutes</span> <strong>${recommended.deqiqe} min</strong></li>
            <li><span>SMS</span> <strong>${recommended.sms}</strong></li>
            <li><span>Duration</span> <strong>${recommended.muddet_gun} days</strong></li>
          </ul>
          <div style="margin-top:12px;">
            <div class="confidence">
              <span class="confidence-dot ${data.confidence > 70 ? 'high' : data.confidence > 40 ? 'medium' : 'low'}"></span>
              AI Confidence: ${data.confidence}%
            </div>
          </div>
        </div>
        ` : `
        <div class="tariff-card" style="display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <div style="font-size:48px;margin-bottom:12px;">✅</div>
          <div class="tariff-name">Your Current Plan is Optimal</div>
          <p style="color:var(--text-secondary);text-align:center;margin-top:8px;font-size:14px;">
            Based on your usage analysis, ${current.ad} is the best fit for you.
          </p>
        </div>
        `}
      </div>

      <!-- Usage Summary -->
      <div class="card" style="margin-bottom:24px;">
        <div class="card-header"><div class="card-title">Your Usage Summary</div></div>
        <div class="stats-grid">
          <div style="text-align:center;">
            <div style="font-size:24px;font-weight:800;">${usage.internet_used_gb} GB</div>
            <div style="font-size:12px;color:var(--text-muted);">Used / ${usage.projected_monthly_gb} GB projected</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:24px;font-weight:800;">${usage.minutes_used} min</div>
            <div style="font-size:12px;color:var(--text-muted);">Used / ${usage.projected_monthly_minutes} projected</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:24px;font-weight:800;">${usage.package_addon_purchases}</div>
            <div style="font-size:12px;color:var(--text-muted);">Add-on purchases</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:24px;font-weight:800;">${usage.period_pct_used}%</div>
            <div style="font-size:12px;color:var(--text-muted);">Billing period elapsed</div>
          </div>
        </div>
      </div>

      <!-- Reasons -->
      <div class="card">
        <div class="card-header"><div class="card-title">Why This Recommendation?</div></div>
        <ul style="list-style:none;">
          ${data.reasons.map(r => `<li style="padding:8px 0;border-bottom:1px solid var(--border-light);font-size:14px;">✅ ${r}</li>`).join('')}
        </ul>
      </div>
    `;

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error loading recommendation</h3></div>';
  }
}

// ── Predictions Page ────────────────────────────────────────────────────────
async function loadPredictions() {
  if (!currentMsisdn) return;
  const container = document.getElementById('predictionsContent');
  container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    const res = await fetch(`${API}/customers/${currentMsisdn}/predict`);
    const data = await res.json();

    let html = `
      <div class="stats-grid" style="margin-bottom:24px;">
        <div class="card" style="text-align:center;">
          <div class="card-title">Days Left in Cycle</div>
          <div class="card-value" style="color:var(--info);">${data.days_left_in_cycle}</div>
        </div>
        <div class="card" style="text-align:center;">
          <div class="card-title">Daily Internet</div>
          <div class="card-value">${data.daily_usage?.internet_gb || 0}</div>
          <div class="card-subtitle">GB / day</div>
        </div>
        <div class="card" style="text-align:center;">
          <div class="card-title">Daily Minutes</div>
          <div class="card-value">${data.daily_usage?.minutes || 0}</div>
          <div class="card-subtitle">min / day</div>
        </div>
      </div>
    `;

    const predictions = data.predictions || [];
    if (!predictions.length) {
      html += '<div class="card"><div class="empty-state"><div class="empty-icon">✅</div><h3>No predictions</h3><p>Insufficient data to generate predictions.</p></div></div>';
    } else {
      html += predictions.map(p => {
        const icon = p.severity === 'critical' ? '🔴' : p.severity === 'high' ? '🟠' : p.severity === 'medium' ? '🔵' : '🟢';
        return `
          <div class="prediction-card ${p.severity}">
            <span class="prediction-icon">${icon}</span>
            <div class="prediction-content">
              <h4>${formatPredictionType(p.type)}</h4>
              <p>${p.description}</p>
              ${p.expected_date ? `<p style="font-size:12px;color:var(--text-muted);margin-top:4px;">Expected: ${p.expected_date}</p>` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error loading predictions</h3></div>';
  }
}

// ── Comparison Page ─────────────────────────────────────────────────────────
async function loadComparison() {
  if (!currentMsisdn) return;
  const container = document.getElementById('comparisonContent');
  container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    const [compRes, tariffRes] = await Promise.all([
      fetch(`${API}/customers/${currentMsisdn}/compare`),
      fetch(`${API}/tariffs`),
    ]);
    const comparison = await compRes.json();
    const tariffs = await tariffRes.json();

    const current = comparison.current;
    const target = comparison.target;
    const diffs = comparison.differences;

    container.innerHTML = `
      <div class="grid-2" style="margin-bottom:24px;">
        <div class="tariff-card current">
          <div class="tariff-name">${current.ad}</div>
          <div class="tariff-price">${current.qiymet_azn} <span>AZN</span></div>
          <ul class="tariff-features">
            <li><span>Data</span> <strong>${current.internet_gb} GB</strong></li>
            <li><span>Minutes</span> <strong>${current.deqiqe} min</strong></li>
            <li><span>SMS</span> <strong>${current.sms}</strong></li>
            <li><span>Social Media</span> <strong>${current.sosial_media_gb || 0} GB</strong></li>
          </ul>
        </div>
        <div class="tariff-card recommended">
          <div class="tariff-name">${target.ad}</div>
          <div class="tariff-price">${target.qiymet_azn} <span>AZN</span></div>
          <ul class="tariff-features">
            <li><span>Data</span> <strong>${target.internet_gb} GB</strong> <span class="${diffs.internet_gb > 0 ? 'diff-positive' : diffs.internet_gb < 0 ? 'diff-negative' : 'diff-neutral'}">${diffs.internet_gb > 0 ? '+' : ''}${diffs.internet_gb} GB</span></li>
            <li><span>Minutes</span> <strong>${target.deqiqe} min</strong> <span class="${diffs.minutes > 0 ? 'diff-positive' : diffs.minutes < 0 ? 'diff-negative' : 'diff-neutral'}">${diffs.minutes > 0 ? '+' : ''}${diffs.minutes}</span></li>
            <li><span>SMS</span> <strong>${target.sms}</strong> <span class="${diffs.sms > 0 ? 'diff-positive' : diffs.sms < 0 ? 'diff-negative' : 'diff-neutral'}">${diffs.sms > 0 ? '+' : ''}${diffs.sms}</span></li>
            <li><span>Social Media</span> <strong>${target.sosial_media_gb || 0} GB</strong></li>
          </ul>
        </div>
      </div>

      <!-- All Tariffs -->
      <div class="card">
        <div class="card-header"><div class="card-title">All Available Plans</div></div>
        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Plan</th>
                <th>Price</th>
                <th>Data</th>
                <th>Minutes</th>
                <th>SMS</th>
                <th>Social</th>
                <th>Duration</th>
              </tr>
            </thead>
            <tbody>
              ${tariffs.map(t => `
                <tr style="${t.tarif_id === current.tarif_id ? 'background:var(--primary-bg);font-weight:600;' : t.tarif_id === target.tarif_id ? 'background:var(--success-bg);' : ''}">
                  <td>${t.ad} ${t.tarif_id === current.tarif_id ? '<span style="font-size:10px;color:var(--primary);">CURRENT</span>' : ''} ${t.tarif_id === target.tarif_id ? '<span style="font-size:10px;color:var(--success);">RECOMMENDED</span>' : ''}</td>
                  <td>${t.qiymet_azn} AZN</td>
                  <td>${t.internet_gb} GB</td>
                  <td>${t.deqiqe} min</td>
                  <td>${t.sms}</td>
                  <td>${t.sosial_media_gb || 0} GB</td>
                  <td>${t.muddet_gun} days</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error loading comparison</h3></div>';
  }
}

// ── Transactions ────────────────────────────────────────────────────────────
async function loadTransactions() {
  if (!currentMsisdn) return;
  const res = await fetch(`${API}/customers/${currentMsisdn}/transactions`);
  const txs = await res.json();

  const tbody = document.getElementById('transactionTable');
  if (!txs.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--text-muted);">No transactions found</td></tr>';
    return;
  }

  tbody.innerHTML = txs.map(tx => {
    const typeClass = getTxTypeClass(tx.tip);
    const amountClass = tx.mebleg_azn >= 0 ? 'amount-positive' : 'amount-negative';
    const amountStr = tx.mebleg_azn >= 0 ? `+${tx.mebleg_azn.toFixed(2)}` : tx.mebleg_azn.toFixed(2);
    return `
      <tr>
        <td style="white-space:nowrap;">${tx.tarix || '--'}</td>
        <td><span class="tx-type-badge ${typeClass}">${formatTxType(tx.tip)}</span></td>
        <td>${tx.tesvir || '--'}</td>
        <td>${tx.kanal || '--'}</td>
        <td class="${amountClass}">${amountStr} AZN</td>
      </tr>
    `;
  }).join('');
}

// ── AI Chat ─────────────────────────────────────────────────────────────────
function setupChatEnter() {
  const input = document.getElementById('chatInput');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }
}

function clearChat() {
  const container = document.getElementById('chatMessages');
  container.innerHTML = '';
}

function addChatMessage(text, isUser = false) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-message ${isUser ? 'user' : 'ai'}`;
  div.innerHTML = `
    <div class="msg-avatar">${isUser ? '👤' : '🤖'}</div>
    <div class="msg-bubble">${formatChatText(text)}</div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function quickChat(message) {
  document.getElementById('chatInput').value = message;
  sendChatMessage();
}

function addTypingIndicator() {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'chat-message ai';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-bubble" style="color:var(--text-muted);">
      <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>
  `;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
  document.getElementById('typingIndicator')?.remove();
}

async function sendChatMessage() {
  const input = document.getElementById('chatInput');
  if (!input) return;
  const message = input.value.trim();
  if (!message) {
    showToast('Please type a message first.');
    return;
  }
  if (!currentMsisdn) {
    // Try to get from select
    const sel = document.getElementById('customerSelect');
    if (sel && sel.value) {
      currentMsisdn = sel.value;
    } else {
      showToast('Please select a customer first.');
      return;
    }
  }

  input.value = '';
  addChatMessage(message, true);
  addTypingIndicator();

  try {
    const res = await fetch(`${API}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ msisdn: currentMsisdn, message }),
    });
    const data = await res.json();
    removeTypingIndicator();
    addChatMessage(data.response || 'I could not process your request.');
  } catch (err) {
    removeTypingIndicator();
    addChatMessage('Sorry, I encountered an error. Please try again.');
  }
}

// ── Telecom Doctor ──────────────────────────────────────────────────────────
async function runDiagnosis() {
  const input = document.getElementById('diagnoseInput');
  const problem = input.value.trim();
  if (!problem || !currentMsisdn) return;

  const container = document.getElementById('diagnosisResult');
  container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    const res = await fetch(`${API}/ai/diagnose`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ msisdn: currentMsisdn, problem }),
    });
    const data = await res.json();
    const diag = data.diagnosis;

    const confClass = (diag.confidence || 0) > 70 ? 'high' : (diag.confidence || 0) > 40 ? 'medium' : 'low';
    const severityIcon = diag.severity === 'critical' ? '🔴' : diag.severity === 'high' ? '🟠' : diag.severity === 'medium' ? '🔵' : '🟢';

    container.innerHTML = `
      <div class="card" style="margin-bottom:16px;">
        <div class="card-header">
          <div class="card-title">${severityIcon} Diagnosis Result</div>
          <div class="confidence">
            <span class="confidence-dot ${confClass}"></span>
            AI Confidence: ${diag.confidence || 50}%
          </div>
        </div>

        <div class="stats-grid" style="margin-bottom:16px;">
          <div style="text-align:center;">
            <div style="font-size:12px;color:var(--text-muted);text-transform:uppercase;">Issue</div>
            <div style="font-size:18px;font-weight:700;">${diag.issue_name || 'Unknown'}</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:12px;color:var(--text-muted);text-transform:uppercase;">Category</div>
            <div style="font-size:18px;font-weight:700;">${diag.issue_category || 'other'}</div>
          </div>
          <div style="text-align:center;">
            <div style="font-size:12px;color:var(--text-muted);text-transform:uppercase;">Severity</div>
            <div style="font-size:18px;font-weight:700;">${severityIcon} ${diag.severity || 'medium'}</div>
          </div>
        </div>

        <div style="background:var(--bg);border-radius:var(--radius-md);padding:16px;margin-bottom:12px;">
          <div style="font-size:12px;font-weight:600;text-transform:uppercase;color:var(--text-muted);margin-bottom:6px;">Explanation</div>
          <p style="font-size:14px;line-height:1.6;">${diag.explanation || 'No explanation available.'}</p>
        </div>

        <div style="background:var(--success-bg);border-radius:var(--radius-md);padding:16px;">
          <div style="font-size:12px;font-weight:600;text-transform:uppercase;color:var(--success);margin-bottom:6px;">Recommended Action</div>
          <p style="font-size:14px;line-height:1.6;">${diag.recommended_action || 'No action recommended.'}</p>
        </div>
      </div>
    `;

    // Store for escalation
    container.dataset.lastDiagnosis = JSON.stringify(diag);
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error running diagnosis</h3></div>';
  }
}

async function escalateToStaff() {
  const container = document.getElementById('diagnosisResult');
  const lastDiag = container.dataset.lastDiagnosis;

  if (!lastDiag) {
    showToast('Please run a diagnosis first before escalating.');
    return;
  }

  container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

  try {
    const res = await fetch(`${API}/support/escalate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ msisdn: currentMsisdn, diagnosis: JSON.parse(lastDiag) }),
    });
    const data = await res.json();

    container.innerHTML = `
      <div class="escalation-card">
        <div class="escalation-header">
          <span style="font-size:24px;">📞</span>
          <h3>Escalated to Support</h3>
        </div>
        <div class="escalation-detail"><span class="label">Customer</span><span class="value">${data.customer?.name || '--'}</span></div>
        <div class="escalation-detail"><span class="label">Sentiment</span><span class="value">${data.sentiment || '--'}</span></div>
        <div class="escalation-detail"><span class="label">Priority</span><span class="value"><span class="priority-badge ${data.priority || 'medium'}">${(data.priority || 'medium').toUpperCase()}</span></span></div>
        <div class="escalation-detail"><span class="label">Issue Summary</span><span class="value">${data.issue_summary || '--'}</span></div>
        <div class="escalation-detail"><span class="label">Suggested Action</span><span class="value">${data.suggested_action || '--'}</span></div>
        ${data.relevant_data_points?.length ? `
          <div style="margin-top:12px;">
            <div style="font-size:12px;font-weight:600;text-transform:uppercase;color:var(--text-muted);margin-bottom:8px;">Key Data Points</div>
            <ul style="list-style:none;">
              ${data.relevant_data_points.map(d => `<li style="padding:4px 0;font-size:13px;">• ${d}</li>`).join('')}
            </ul>
          </div>
        ` : ''}
      </div>
      <p style="margin-top:12px;font-size:12px;color:var(--text-muted);">A staff member will be notified. You can also visit the <a href="/staff">Staff Dashboard</a>.</p>
    `;
  } catch (err) {
    container.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><h3>Error escalating</h3></div>';
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────
function formatPredictionType(type) {
  const map = {
    internet_exhaustion: '📶 Data Running Low',
    internet_sufficient: '✅ Data Sufficient',
    internet_depleted: '🚫 Data Depleted',
    minutes_exhaustion: '📞 Minutes Running Low',
    balance_depletion: '💰 Balance Depleting',
    addon_trend: '📦 Frequent Add-on Purchases',
  };
  return map[type] || type;
}

function formatTxType(tip) {
  const map = {
    balans_artirma: 'Top-up',
    tarif_yenilenmesi: 'Renewal',
    tarif_deyisikliyi: 'Change',
    paket_alisi: 'Add-on',
    paketdenkenar_sms: 'Extra SMS',
    paketdenkenar_zeng: 'Extra Call',
    balans_yoxlama_ussd: 'Check',
  };
  return map[tip] || tip;
}

function getTxTypeClass(tip) {
  if (tip.includes('artirma')) return 'topup';
  if (tip.includes('yenilenmesi')) return 'renewal';
  if (tip.includes('deyisikliyi')) return 'change';
  if (tip.includes('paket_alisi')) return 'package';
  if (tip.includes('paketdenkenar')) return 'oop';
  return 'check';
}

function formatChatText(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
