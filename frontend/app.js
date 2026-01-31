const form = document.getElementById("analysisForm");
const statusEl = document.getElementById("status");
const statsEl = document.getElementById("stats");
const graphFrame = document.getElementById("graphFrame");
const reportTable = document.getElementById("reportTable");
const reportDownload = document.getElementById("reportDownload");

const setStatus = (message, isError = false) => {
  statusEl.textContent = message;
  statusEl.className = isError ? "status error" : "status";
};

const renderStats = (stats) => {
  if (!stats) {
    statsEl.textContent = "";
    return;
  }
  statsEl.innerHTML = `
    <div><strong>Transactions:</strong> ${stats.transactions}</div>
    <div><strong>Wallets:</strong> ${stats.wallets}</div>
    <div><strong>Edges:</strong> ${stats.edges}</div>
    <div><strong>Subgraph Nodes:</strong> ${stats.subgraph_nodes}</div>
    <div><strong>Subgraph Edges:</strong> ${stats.subgraph_edges}</div>
    <div><strong>Illicit Seeds:</strong> ${stats.illicit_seeds}</div>
  `;
};

const renderReport = (rows) => {
  if (!rows || rows.length === 0) {
    reportTable.innerHTML = "<p>No report data available.</p>";
    return;
  }

  const headers = Object.keys(rows[0]);
  const headerRow = headers.map((h) => `<th>${h}</th>`).join("");
  const bodyRows = rows
    .map(
      (row) =>
        `<tr>${headers
          .map((h) => `<td>${row[h] ?? ""}</td>`)
          .join("")}</tr>`
    )
    .join("");

  reportTable.innerHTML = `
    <table>
      <thead><tr>${headerRow}</tr></thead>
      <tbody>${bodyRows}</tbody>
    </table>
  `;
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const transactions = document.getElementById("transactions").files[0];
  const illicitWallets = document.getElementById("illicitWallets").files[0];

  if (!transactions) {
    setStatus("Please select a transactions CSV file.", true);
    return;
  }

  const formData = new FormData();
  formData.append("transactions", transactions);
  if (illicitWallets) {
    formData.append("illicit_wallets", illicitWallets);
  }

  setStatus("Running analysis...");
  renderStats(null);
  reportTable.innerHTML = "";
  reportDownload.hidden = true;
  graphFrame.removeAttribute("src");

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || response.statusText);
    }

    const data = await response.json();
    setStatus("Analysis complete.");
    renderStats(data.stats);
    renderReport(data.report);

    if (data.graph_url) {
      graphFrame.src = data.graph_url;
    }

    if (data.report_url) {
      reportDownload.href = data.report_url;
      reportDownload.hidden = false;
    }
  } catch (error) {
    setStatus(`Error: ${error.message}`, true);
  }
});
