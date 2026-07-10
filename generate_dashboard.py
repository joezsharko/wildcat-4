#!/usr/bin/env python3
"""
Builds a self-contained dashboard.html from prices.db.
Data is embedded directly in the file so it works by just double-clicking
it open in a browser -- no local server required.
"""

import json
import os
import sqlite3

DB_PATH = "data/prices.db"
OUT_PATH = "docs/index.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>New Inventory Tracker — McGrath City Mazda</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<style>
  :root {
    --navy: #14213D;
    --navy-light: #24345C;
    --amber: #E8A33D;
    --paper: #F7F6F3;
    --line: #DCD9D2;
    --up: #C1442D;
    --down: #2F7A4F;
    --ink: #1A1A1A;
    --ink-soft: #5B5B57;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: 'Courier New', Courier, monospace;
  }
  header {
    background: var(--navy);
    color: white;
    padding: 28px 32px 22px;
    border-bottom: 4px solid var(--amber);
  }
  header .eyebrow {
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--amber);
    margin: 0 0 6px;
  }
  header h1 {
    margin: 0;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  header .sub {
    margin: 6px 0 0;
    color: #C7CEDD;
    font-size: 13px;
  }
  main { max-width: 1080px; margin: 0 auto; padding: 24px 32px 60px; }
  .stat-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 28px;
  }
  .stat {
    background: white;
    border: 1px solid var(--line);
    padding: 16px 18px;
  }
  .stat .label {
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 6px;
  }
  .stat .value {
    font-size: 24px;
    font-weight: 700;
    color: var(--navy);
  }
  section { margin-bottom: 34px; }
  h2 {
    font-size: 14px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--navy);
    border-bottom: 2px solid var(--navy);
    padding-bottom: 8px;
    margin-bottom: 16px;
  }
  .chart-box {
    background: white;
    border: 1px solid var(--line);
    padding: 18px;
  }
  select {
    font-family: inherit;
    padding: 6px 10px;
    border: 1px solid var(--line);
    background: white;
    margin-bottom: 14px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    font-size: 13px;
  }
  th, td {
    text-align: left;
    padding: 9px 10px;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }
  th {
    background: var(--navy);
    color: white;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    position: sticky; top: 0;
  }
  td.price { font-weight: 700; }
  .delta-up { color: var(--up); }
  .delta-down { color: var(--down); }
  .delta-none { color: var(--ink-soft); }
  .table-wrap { max-height: 480px; overflow-y: auto; border: 1px solid var(--line); }
  .table-wrap table { border: none; }
  footer {
    max-width: 1080px; margin: 0 auto; padding: 0 32px 40px;
    color: var(--ink-soft); font-size: 12px;
  }
</style>
</head>
<body>

<header>
  <p class="eyebrow">Price Tracker &middot; Prototype</p>
  <h1>McGrath City Mazda — New Inventory</h1>
  <p class="sub">Tracking MSRP and "Your Price" across new inventory over time. Last updated: <span id="lastUpdated"></span></p>
</header>

<main>
  <div class="stat-row">
    <div class="stat"><div class="label">Vehicles Tracked</div><div class="value" id="statVehicles">—</div></div>
    <div class="stat"><div class="label">Snapshots Taken</div><div class="value" id="statSnapshots">—</div></div>
    <div class="stat"><div class="label">Avg. Your Price</div><div class="value" id="statAvgPrice">—</div></div>
    <div class="stat"><div class="label">Price Drops Detected</div><div class="value" id="statDrops">—</div></div>
  </div>

  <section>
    <h2>Average Price Over Time</h2>
    <select id="modelFilter"></select>
    <div class="chart-box">
      <canvas id="priceChart" height="90"></canvas>
    </div>
  </section>

  <section>
    <h2>Current Inventory (Latest Snapshot)</h2>
    <div class="table-wrap">
      <table id="inventoryTable">
        <thead>
          <tr>
            <th>Year</th><th>Model</th><th>VIN</th><th>Stock #</th>
            <th>MSRP</th><th>Your Price</th><th>Change</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
  </section>
</main>

<footer>
  Data scraped from mcgrathcitymazda.com inventory pages. For personal tracking use only.
</footer>

<script>
const RAW_DATA = __DATA_JSON__;

function fmtMoney(n) {
  if (n === null || n === undefined) return "—";
  return "$" + n.toLocaleString();
}

// Group rows by scraped_at (one snapshot) and by vin
const byVin = {};
const snapshotTimes = [...new Set(RAW_DATA.map(r => r.scraped_at))].sort();

RAW_DATA.forEach(r => {
  if (!byVin[r.vin]) byVin[r.vin] = [];
  byVin[r.vin].push(r);
});

// ---- Stats ----
document.getElementById('statVehicles').textContent = Object.keys(byVin).length;
document.getElementById('statSnapshots').textContent = snapshotTimes.length;

const latestTime = snapshotTimes[snapshotTimes.length - 1];
const latestRows = RAW_DATA.filter(r => r.scraped_at === latestTime);
const avgPrice = latestRows.length
  ? Math.round(latestRows.reduce((s, r) => s + (r.your_price || 0), 0) / latestRows.length)
  : null;
document.getElementById('statAvgPrice').textContent = fmtMoney(avgPrice);
document.getElementById('lastUpdated').textContent = latestTime
  ? new Date(latestTime).toLocaleString()
  : "no data yet";

let dropCount = 0;
Object.values(byVin).forEach(rows => {
  for (let i = 1; i < rows.length; i++) {
    if (rows[i].your_price !== null && rows[i-1].your_price !== null &&
        rows[i].your_price < rows[i-1].your_price) dropCount++;
  }
});
document.getElementById('statDrops').textContent = dropCount;

// ---- Model filter ----
const models = [...new Set(RAW_DATA.map(r => r.model))].sort();
const modelSelect = document.getElementById('modelFilter');
modelSelect.innerHTML = '<option value="__all__">All Models (avg)</option>' +
  models.map(m => `<option value="${m}">${m}</option>`).join('');

// ---- Chart ----
let chart;
function renderChart(modelFilter) {
  const labels = snapshotTimes.map(t => new Date(t).toLocaleDateString());
  const data = snapshotTimes.map(t => {
    const rows = RAW_DATA.filter(r => r.scraped_at === t &&
      (modelFilter === '__all__' || r.model === modelFilter));
    if (!rows.length) return null;
    return Math.round(rows.reduce((s, r) => s + (r.your_price || 0), 0) / rows.length);
  });

  if (chart) chart.destroy();
  const ctx = document.getElementById('priceChart').getContext('2d');
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: modelFilter === '__all__' ? 'Avg. Your Price (all models)' : `Avg. Your Price — ${modelFilter}`,
        data,
        borderColor: '#14213D',
        backgroundColor: 'rgba(232,163,61,0.15)',
        pointBackgroundColor: '#E8A33D',
        borderWidth: 2,
        tension: 0.15,
        fill: true,
        spanGaps: true,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } },
      scales: {
        y: { ticks: { callback: v => '$' + v.toLocaleString() } }
      }
    }
  });
}
renderChart('__all__');
modelSelect.addEventListener('change', e => renderChart(e.target.value));

// ---- Inventory table (latest snapshot, with change vs. prior snapshot) ----
const tbody = document.querySelector('#inventoryTable tbody');
const priorTime = snapshotTimes.length > 1 ? snapshotTimes[snapshotTimes.length - 2] : null;

latestRows
  .sort((a, b) => (a.your_price || 0) - (b.your_price || 0))
  .forEach(r => {
    const priorRow = priorTime
      ? RAW_DATA.find(x => x.scraped_at === priorTime && x.vin === r.vin)
      : null;
    let deltaHtml = '<span class="delta-none">—</span>';
    if (priorRow && priorRow.your_price !== null && r.your_price !== null) {
      const diff = r.your_price - priorRow.your_price;
      if (diff < 0) deltaHtml = `<span class="delta-down">▼ ${fmtMoney(Math.abs(diff))}</span>`;
      else if (diff > 0) deltaHtml = `<span class="delta-up">▲ ${fmtMoney(diff)}</span>`;
      else deltaHtml = '<span class="delta-none">no change</span>';
    }
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.year}</td>
      <td>${r.model}</td>
      <td>${r.vin}</td>
      <td>${r.stock_number}</td>
      <td class="price">${fmtMoney(r.msrp)}</td>
      <td class="price">${fmtMoney(r.your_price)}</td>
      <td>${deltaHtml}</td>
    `;
    tbody.appendChild(tr);
  });
</script>
</body>
</html>
"""


def generate(db_path: str = DB_PATH, out_path: str = OUT_PATH):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Table may not exist yet on a brand-new DB (first-ever run)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at TEXT NOT NULL,
            vin TEXT NOT NULL,
            year TEXT,
            model TEXT,
            stock_number TEXT,
            exterior_color TEXT,
            interior_color TEXT,
            msrp INTEGER,
            your_price INTEGER
        )
    """)
    rows = conn.execute(
        "SELECT * FROM price_snapshots ORDER BY scraped_at ASC"
    ).fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    html = TEMPLATE.replace("__DATA_JSON__", json.dumps(data))

    with open(out_path, "w") as f:
        f.write(html)
    return out_path


if __name__ == "__main__":
    path = generate()
    print(f"Dashboard written to {path}")
