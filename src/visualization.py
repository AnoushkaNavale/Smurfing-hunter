"""
Visualization Module
Creates interactive PyVis graph visualizations.
"""

from pathlib import Path

import numpy as np
from pyvis.network import Network


GRAPH_LOADING_THEME = """
<style>
  body {
    background: #111821 !important;
  }

  #mynetwork {
    background:
      radial-gradient(circle at 24% 18%, rgba(155, 124, 255, 0.16), transparent 34%),
      radial-gradient(circle at 80% 8%, rgba(255, 92, 154, 0.13), transparent 28%),
      #111821 !important;
  }

  #loadingBar {
    background:
      radial-gradient(circle at 30% 20%, rgba(73, 214, 200, 0.18), transparent 30%),
      rgba(17, 24, 33, 0.88) !important;
    backdrop-filter: blur(18px);
    transition: opacity 500ms ease;
  }

  #loadingBar .outerBorder {
    width: min(560px, calc(100% - 48px)) !important;
    height: 92px !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    border: 1px solid rgba(160, 176, 200, 0.22) !important;
    border-radius: 24px !important;
    background: rgba(28, 37, 51, 0.9) !important;
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.34) !important;
  }

  #loadingBar .outerBorder::before {
    content: "Building GNN wallet graph";
    display: block;
    margin: 18px 22px 10px;
    color: #f6f8fb;
    font-family: Inter, "Segoe UI", Arial, sans-serif;
    font-size: 14px;
    font-weight: 900;
  }

  #loadingBar #border {
    width: calc(100% - 112px) !important;
    height: 14px !important;
    margin-left: 22px !important;
    border: 1px solid rgba(160, 176, 200, 0.22) !important;
    border-radius: 999px !important;
    background: rgba(17, 24, 33, 0.78) !important;
    overflow: hidden !important;
  }

  #loadingBar #bar {
    height: 100% !important;
    border-radius: 999px !important;
    background: linear-gradient(90deg, #49d6c8, #9b7cff, #ff5c9a) !important;
    box-shadow: 0 0 24px rgba(73, 214, 200, 0.32) !important;
  }

  #loadingBar #text {
    position: absolute !important;
    right: 22px !important;
    bottom: 21px !important;
    color: #f6f8fb !important;
    font-family: Inter, "Segoe UI", Arial, sans-serif !important;
    font-size: 15px !important;
    font-weight: 900 !important;
  }
</style>
"""


def _theme_graph_loading_bar(output_file):
    path = Path(output_file)
    try:
        html = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        html = path.read_text()

    if "Building GNN wallet graph" in html:
        return

    if "</head>" in html:
        html = html.replace("</head>", f"{GRAPH_LOADING_THEME}\n</head>", 1)
    else:
        html = GRAPH_LOADING_THEME + html

    path.write_text(html, encoding="utf-8")


def visualize_laundering_graph(
    subgraph,
    wallet_scores,
    illicit_seeds,
    output_file="laundering_graph.html",
    open_browser=True,
):
    """
    Create interactive PyVis visualization.
    """
    net = Network(height="800px", width="100%", directed=True, notebook=False)
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)

    for node in subgraph.nodes():
        score = wallet_scores.get(node, {}).get("total", 0)
        probability = wallet_scores.get(node, {}).get("gnn_probability", 0)

        if node in illicit_seeds:
            color = "#FF0000"
            title = f"ILLICIT SEED: {node}"
            size = 40
        elif score >= 75:
            color = "#FF6600"
            title = f"HIGH RISK: {node}"
            size = 30
        elif score >= 50:
            color = "#FFA500"
            title = f"MEDIUM RISK: {node}"
            size = 25
        else:
            color = "#90EE90"
            title = f"LOW RISK: {node}"
            size = 20

        title_parts = [
            title,
            f"Score: {score:.1f}",
            f"GNN probability: {probability:.3f}",
        ]
        title = " | ".join(title_parts)

        net.add_node(node, label=node[:8], title=title, color=color, size=size)

    for src, dst, data in subgraph.edges(data=True):
        total_amount = data["total_amount"]
        count = data["count"]
        token_types = ", ".join(data.get("token_types", [])) or "unknown"
        width = min(1 + np.log10(total_amount + 1) * 2, 10)
        title = (
            f"{src[:8]} -> {dst[:8]} | Amount: {total_amount:.4f} | "
            f"Txs: {count} | Tokens: {token_types}"
        )
        net.add_edge(src, dst, width=width, title=title, arrows="to")

    net.write_html(output_file, open_browser=False, notebook=False)
    _theme_graph_loading_bar(output_file)
    print(f"Visualization saved to {output_file}")
    if open_browser:
        try:
            import webbrowser

            webbrowser.open(output_file)
        except Exception:
            pass
