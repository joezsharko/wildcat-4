// Shared helpers for all dashboard pages. Loaded via <script src="common.js">
// before each page's own inline script.

function fmtMoney(n) {
  if (n === null || n === undefined) return "—";
  return "$" + n.toLocaleString();
}

function fmtDays(days) {
  if (days === null || days === undefined) return "—";
  return days === 1 ? "1 day" : `${days} days`;
}

function fmtDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString([], {
    year: "numeric", month: "short", day: "numeric",
    hour: "numeric", minute: "2-digit"
  });
}

// "Model" = base nameplate (CX-30, MAZDA3, etc); "Trim" = the full
// model+trim string as scraped (e.g. "CX-30 2.5 S Select Sport AWD").
// Longer/more-specific names must be checked first so e.g. "CX-50" isn't
// misread as "CX-5".
const KNOWN_BASE_MODELS = ['CX-30', 'CX-50', 'CX-70', 'CX-90', 'CX-5', 'MX-5', 'MAZDA3', 'MAZDA6'];
function extractBaseModel(fullModel) {
  const upper = (fullModel || '').toUpperCase();
  for (const base of KNOWN_BASE_MODELS) {
    if (upper.startsWith(base)) return base;
  }
  return (fullModel || '').split(' ')[0] || 'Unknown';
}

// Fetches data.json and tracking.json (same directory as the page).
// Returns a Promise resolving to {rawData, trackingData}.
async function loadDashboardData() {
  const [rawResp, trackingResp] = await Promise.all([
    fetch('data.json'),
    fetch('tracking.json'),
  ]);
  const rawData = await rawResp.json();
  const trackingData = await trackingResp.json();
  return { rawData, trackingData };
}

// Generic click-to-sort for a <table>. Pass the table element and a
// function (rowIndex) => the array of data rows currently rendered, plus
// a render(rows) function that rebuilds tbody from a (possibly resorted)
// rows array. Attaches sort-on-click to every <th data-sort-key="...">.
function makeSortable(table, getRows, render) {
  let currentKey = null;
  let ascending = true;

  table.querySelectorAll('th[data-sort-key]').forEach(th => {
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const key = th.getAttribute('data-sort-key');
      if (key === currentKey) {
        ascending = !ascending;
      } else {
        currentKey = key;
        ascending = true;
      }

      table.querySelectorAll('th[data-sort-key]').forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(ascending ? 'sort-asc' : 'sort-desc');

      const rows = getRows();
      rows.sort((a, b) => {
        let av = a[key], bv = b[key];
        if (av === null || av === undefined) av = ascending ? Infinity : -Infinity;
        if (bv === null || bv === undefined) bv = ascending ? Infinity : -Infinity;
        if (typeof av === 'string') av = av.toLowerCase();
        if (typeof bv === 'string') bv = bv.toLowerCase();
        if (av < bv) return ascending ? -1 : 1;
        if (av > bv) return ascending ? 1 : -1;
        return 0;
      });
      render(rows);
    });
  });
}
