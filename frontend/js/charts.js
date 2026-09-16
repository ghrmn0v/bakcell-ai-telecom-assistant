/* ═══════════════════════════════════════════════════════════════════════════
   Charts Configuration — Chart.js
   ═══════════════════════════════════════════════════════════════════════════ */

let spendingChartInstance = null;

function renderSpendingChart(dailySpend) {
  const ctx = document.getElementById('spendingChart');
  if (!ctx) return;

  // Destroy previous chart
  if (spendingChartInstance) {
    spendingChartInstance.destroy();
  }

  // Sort by date
  const sorted = Object.entries(dailySpend)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-30); // Last 30 days

  if (sorted.length === 0) {
    // No data
    const parent = ctx.parentElement;
    parent.innerHTML = '<div class="empty-state"><div class="empty-icon">📊</div><h3>No spending data</h3><p>Transaction data will appear here.</p></div>';
    return;
  }

  const labels = sorted.map(([date]) => {
    const d = new Date(date);
    return d.toLocaleDateString('en', { day: 'numeric', month: 'short' });
  });
  const values = sorted.map(([, val]) => Math.abs(val));

  // Cumulative spending
  let cumulative = 0;
  const cumulativeValues = values.map(v => {
    cumulative += v;
    return Math.round(cumulative * 100) / 100;
  });

  spendingChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Daily Spending (AZN)',
          data: values,
          backgroundColor: 'rgba(227, 6, 19, 0.15)',
          borderColor: 'rgba(227, 6, 19, 0.8)',
          borderWidth: 1,
          borderRadius: 4,
          order: 2,
        },
        {
          label: 'Cumulative (AZN)',
          data: cumulativeValues,
          type: 'line',
          borderColor: '#3B82F6',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.3,
          order: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index',
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            font: { size: 11, family: 'Inter' },
            padding: 16,
          },
        },
        tooltip: {
          backgroundColor: '#1A1A2E',
          titleFont: { family: 'Inter', size: 12 },
          bodyFont: { family: 'Inter', size: 12 },
          padding: 10,
          cornerRadius: 8,
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 10, family: 'Inter' },
            maxRotation: 45,
            autoSkip: true,
            maxTicksLimit: 15,
          },
        },
        y: {
          grid: { color: '#F3F4F6' },
          ticks: {
            font: { size: 10, family: 'Inter' },
            callback: (val) => `${val}₼`,
          },
        },
      },
    },
  });
}
