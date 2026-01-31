"""
Visualization Module
Creates interactive PyVis graph visualizations
"""

from pyvis.network import Network
import numpy as np

def visualize_laundering_graph(
    subgraph,
    wallet_scores,
    illicit_seeds,
    output_file='laundering_graph.html'
):
    """
    Create interactive PyVis visualization
    """
    net = Network(height='800px', width='100%', directed=True, notebook=False)
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)

    for node in subgraph.nodes():
        score = wallet_scores.get(node, {}).get('total', 0)

        if node in illicit_seeds:
            color = '#FF0000'
            title = f"ILLICIT SEED: {node}"
            size = 40
        elif score > 15:
            color = '#FF6600'
            title = f"HIGH RISK: {node}<br>Score: {score:.1f}"
            size = 30
        elif score > 8:
            color = '#FFA500'
            title = f"MEDIUM RISK: {node}<br>Score: {score:.1f}"
            size = 25
        else:
            color = '#90EE90'
            title = f"LOW RISK: {node}<br>Score: {score:.1f}"
            size = 20

        net.add_node(
            node,
            label=node[:8],
            title=title,
            color=color,
            size=size
        )

    for src, dst, data in subgraph.edges(data=True):
        total_amount = data.get('total_amount', 0)
        count = data.get('count', 0)

        width = min(1 + np.log10(total_amount + 1) * 2, 10)
        title = (
            f"{src[:8]} → {dst[:8]}<br>"
            f"Amount: {total_amount:.4f}<br>"
            f"Txs: {count}"
        )

        net.add_edge(src, dst, width=width, title=title, arrows='to')

    # Safe HTML write (works in hackathon demos)
    net.write_html(output_file, open_browser=False, notebook=False)
    print(f"✅ Visualization saved to {output_file}")

    try:
        import webbrowser
        webbrowser.open(output_file)
    except Exception:
        pass
