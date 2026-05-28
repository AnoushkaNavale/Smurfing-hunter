const { createElement: h, useEffect, useMemo, useState } = React;

const navItems = [
  { id: "overview", label: "Overview" },
  { id: "graph", label: "Graph" },
  { id: "report", label: "Report" },
];

const statLabels = [
  ["transactions", "Transactions"],
  ["wallets", "Wallets"],
  ["edges", "Edges"],
  ["subgraph_nodes", "Subgraph Nodes"],
  ["subgraph_edges", "Subgraph Edges"],
  ["illicit_seeds", "Illicit Seeds"],
];

function App() {
  const [activeView, setActiveView] = useState("overview");
  const [theme, setTheme] = useState(
    localStorage.getItem("smurfingHunterTheme") || "dark"
  );
  const [transactionsFile, setTransactionsFile] = useState(null);
  const [illicitFile, setIllicitFile] = useState(null);
  const [status, setStatus] = useState("Ready for CSV upload.");
  const [isError, setIsError] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("smurfingHunterTheme", theme);
  }, [theme]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [activeView]);

  const reportRows = analysis?.report || [];
  const stats = analysis?.stats || null;

  const statusClass = `status${isError ? " error" : ""}`;
  const themeLabel = theme === "light" ? "Light" : "Dark";

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!transactionsFile) {
      setStatus("Please select a transactions CSV file.");
      setIsError(true);
      return;
    }

    const formData = new FormData();
    formData.append("transactions", transactionsFile);
    if (illicitFile) {
      formData.append("illicit_wallets", illicitFile);
    }

    setIsRunning(true);
    setIsError(false);
    setStatus("Running GNN analysis...");
    setAnalysis(null);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);
      const response = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => ({}));
        throw new Error(errorPayload.detail || response.statusText);
      }

      const payload = await response.json();
      setAnalysis(payload);
      setStatus("Analysis complete.");
      setActiveView("overview");
    } catch (error) {
      const message =
        error.name === "AbortError"
          ? "Analysis took too long. Try a smaller CSV or run the CLI for a large dataset."
          : error.message;
      setStatus(`Error: ${message}`);
      setIsError(true);
    } finally {
      setIsRunning(false);
    }
  };

  return h(
    "main",
    { className: "dashboard-shell" },
    h(
      "aside",
      { className: "sidebar", "aria-label": "Application navigation" },
      h(
        "nav",
        { className: "nav-stack" },
        navItems.map((item) =>
          h(
            "button",
            {
              key: item.id,
              className: `nav-item${activeView === item.id ? " active" : ""}`,
              type: "button",
              onClick: () => setActiveView(item.id),
            },
            item.label
          )
        )
      )
    ),
    h(
      "section",
      { className: "main-stage" },
      h(
        "header",
        { className: "topbar" },
        h(
          "div",
          null,
          h("p", { className: "eyebrow" }, "Crypto-forensics graph neural network"),
          h("h1", null, "Smurfing-hunter"),
          h(
            "p",
            { className: "subtitle" },
            "Train on transaction ledgers and illicit seed wallets to rank wallet-level laundering risk."
          )
        ),
        h(
          "div",
          { className: "topbar-actions" },
          h(
            "label",
            { className: "theme-toggle", htmlFor: "themeToggle" },
            h("input", {
              type: "checkbox",
              id: "themeToggle",
              checked: theme === "light",
              onChange: () => setTheme(theme === "light" ? "dark" : "light"),
            }),
            h("span", { className: "toggle-track" }, h("span", { className: "toggle-thumb" })),
            h("span", { className: "theme-label" }, themeLabel)
          ),
          h(
            "div",
            { className: "topbar-badge" },
            h("span", { className: "badge-dot" }),
            "GNN AML scoring"
          )
        )
      ),
      h(UploadPanel, {
        transactionsFile,
        illicitFile,
        onTransactionsChange: setTransactionsFile,
        onIllicitChange: setIllicitFile,
        onSubmit: handleSubmit,
        isRunning,
        status,
        statusClass,
      }),
      h(
        "div",
        { className: `view-pane${activeView === "overview" ? " is-active" : ""}` },
        h(OverviewView, { stats, analysis, reportRows, setActiveView })
      ),
      h(
        "div",
        { className: `view-pane${activeView === "graph" ? " is-active" : ""}` },
        h(GraphView, { analysis })
      ),
      h(
        "div",
        { className: `view-pane${activeView === "report" ? " is-active" : ""}` },
        h(ReportView, { analysis, reportRows })
      )
    )
  );
}

function UploadPanel({
  transactionsFile,
  illicitFile,
  onTransactionsChange,
  onIllicitChange,
  onSubmit,
  isRunning,
  status,
  statusClass,
}) {
  return h(
    "section",
    { className: "control-panel" },
    h(
      "form",
      { className: "upload-grid", onSubmit },
      h(
        "label",
        { className: "file-field" },
        h("span", null, "Transactions CSV"),
        h("small", null, "Required transaction edge list"),
        h("input", {
          type: "file",
          accept: ".csv",
          required: true,
          onChange: (event) => onTransactionsChange(event.target.files[0] || null),
        }),
        transactionsFile &&
          h("strong", { className: "file-name" }, transactionsFile.name)
      ),
      h(
        "label",
        { className: "file-field" },
        h("span", null, "Illicit wallets CSV"),
        h("small", null, "Optional seed wallet list"),
        h("input", {
          type: "file",
          accept: ".csv",
          onChange: (event) => onIllicitChange(event.target.files[0] || null),
        }),
        illicitFile && h("strong", { className: "file-name" }, illicitFile.name)
      ),
      h(
        "div",
        { className: "actions" },
        h("button", { type: "submit", disabled: isRunning }, isRunning ? "Analyzing..." : "Run Analysis"),
        h("p", { className: statusClass }, status)
      )
    )
  );
}

function OverviewView({ stats, analysis, reportRows, setActiveView }) {
  const topRisk = reportRows[0];

  return h(
    "section",
    { className: "view-grid overview-grid" },
    h(
      "div",
      { className: "surface overview-main" },
      h(
        "div",
        { className: "section-header" },
        h(
          "div",
          null,
          h("p", { className: "section-kicker" }, "Overview"),
          h("h2", null, "GNN Analysis Summary")
        )
      ),
      stats
        ? h(StatsGrid, { stats })
        : h(
            "div",
            { className: "empty-state" },
            h("h3", null, "Upload CSV files to begin"),
            h(
              "p",
              null,
              "After analysis, this view shows transaction scale, graph size, seed count, and highest-risk wallet output."
            )
          ),
      stats &&
        h(
          "div",
          { className: "insight-grid" },
          h(
            "article",
            { className: "insight-card" },
            h("span", null, "Top Risk Wallet"),
            h("strong", null, topRisk?.Wallet || "Not available"),
            h("p", null, topRisk ? `Score ${topRisk.Score} with probability ${topRisk.GNN_Probability}.` : "")
          ),
          h(
            "article",
            { className: "insight-card" },
            h("span", null, "Model"),
            h("strong", null, "Two-layer GCN"),
            h("p", null, "Learns from wallet features and neighboring wallet behavior.")
          ),
          h(
            "article",
            { className: "insight-card" },
            h("span", null, "Training Labels"),
            h("strong", null, `${stats.illicit_seeds} seeds`),
            h("p", null, "Known illicit wallets are used as positive GNN labels.")
          )
        )
    ),
    h(
      "div",
      { className: "surface details-panel" },
      h("p", { className: "section-kicker" }, "How to read it"),
      h("h2", null, "What the score means"),
      h(
        "p",
        null,
        "The GNN probability estimates how similar a wallet is to illicit seed regions after message passing over the transaction graph."
      ),
      h(
        "div",
        { className: "detail-list" },
        h("div", null, h("strong", null, "75-100"), h("span", null, "High risk")),
        h("div", null, h("strong", null, "50-74"), h("span", null, "Elevated risk")),
        h("div", null, h("strong", null, "0-49"), h("span", null, "Lower risk"))
      ),
      h(
        "div",
        { className: "quick-actions" },
        h("button", { type: "button", onClick: () => setActiveView("graph") }, "Open Graph"),
        h("button", { type: "button", onClick: () => setActiveView("report") }, "Open Report")
      )
    )
  );
}

function StatsGrid({ stats }) {
  return h(
    "div",
    { className: "stats" },
    statLabels.map(([key, label]) =>
      h(
        "div",
        { className: "stat-card", key },
        h("span", { className: "stat-label" }, label),
        h("span", { className: "stat-value" }, stats[key] ?? 0)
      )
    )
  );
}

function GraphView({ analysis }) {
  return h(
    "section",
    { className: "view-grid graph-grid" },
    h(
      "div",
      { className: "surface graph-surface" },
      h(
        "div",
        { className: "section-header" },
        h("div", null, h("p", { className: "section-kicker" }, "Network view"), h("h2", null, "Laundering Graph"))
      ),
      analysis?.graph_url
        ? h("iframe", { src: analysis.graph_url, title: "Laundering graph" })
        : h("div", { className: "empty-state tall" }, h("h3", null, "No graph yet"), h("p", null, "Run analysis to generate the interactive wallet graph."))
    ),
    h(
      "aside",
      { className: "surface details-panel" },
      h("p", { className: "section-kicker" }, "Graph details"),
      h("h2", null, "Node interpretation"),
      h(
        "div",
        { className: "legend-list" },
        h("div", null, h("i", { className: "legend red" }), h("span", null, "Known illicit seed wallet")),
        h("div", null, h("i", { className: "legend orange" }), h("span", null, "High GNN risk wallet")),
        h("div", null, h("i", { className: "legend amber" }), h("span", null, "Elevated GNN risk wallet")),
        h("div", null, h("i", { className: "legend green" }), h("span", null, "Lower GNN risk wallet"))
      ),
      h("p", null, "Node size follows the learned risk score. Edge width follows transaction volume.")
    )
  );
}

function ReportView({ analysis, reportRows }) {
  const totalRows = analysis?.report_count || 0;
  const headers = useMemo(() => (reportRows[0] ? Object.keys(reportRows[0]) : []), [reportRows]);

  return h(
    "section",
    { className: "surface report-surface full-report" },
    h(
      "div",
      { className: "section-header" },
      h("div", null, h("p", { className: "section-kicker" }, "Risk ranking"), h("h2", null, "Suspicion Report")),
      analysis?.report_url &&
        h("a", { className: "link", href: analysis.report_url, download: true }, "Download CSV")
    ),
    reportRows.length
      ? h(
          "div",
          { className: "table" },
          totalRows > reportRows.length &&
            h("p", { className: "table-note" }, `Showing top ${reportRows.length} of ${totalRows} wallets. Download CSV for the full report.`),
          h(
            "table",
            null,
            h("thead", null, h("tr", null, headers.map((header) => h("th", { key: header }, header)))),
            h(
              "tbody",
              null,
              reportRows.map((row, index) =>
                h(
                  "tr",
                  { key: `${row.Wallet}-${index}` },
                  headers.map((header) => h("td", { key: header }, row[header] ?? ""))
                )
              )
            )
          )
        )
      : h("div", { className: "empty-state tall" }, h("h3", null, "No report yet"), h("p", null, "Run analysis to generate GNN wallet rankings."))
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
