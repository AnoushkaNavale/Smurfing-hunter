"""
Graph Builder Module
Constructs directed transaction graph from transaction data
"""

import networkx as nx


def build_transaction_graph(df):
    """
    Construct directed graph from transaction DataFrame
    
    Args:
        df: pandas DataFrame with columns: src_wallet, dst_wallet, amount, timestamp
        
    Returns:
        NetworkX DiGraph with transaction metadata on edges
    """
    G = nx.DiGraph()
    
    for _, row in df.iterrows():
        src = row['src_wallet']
        dst = row['dst_wallet']
        amount = row['amount']
        timestamp = row['timestamp']
        
        if not G.has_edge(src, dst):
            G.add_edge(src, dst, transactions=[])
        
        G[src][dst]['transactions'].append({
            'amount': amount,
            'timestamp': timestamp,
            'token_type': row.get('token_type')
        })
    
    for src, dst in G.edges():
        txs = G[src][dst]['transactions']
        G[src][dst]['total_amount'] = sum(t['amount'] for t in txs)
        G[src][dst]['count'] = len(txs)
        G[src][dst]['timestamps'] = [t['timestamp'] for t in txs]
        G[src][dst]['amounts'] = [t['amount'] for t in txs]
        G[src][dst]['token_types'] = sorted(
            {str(t['token_type']) for t in txs if t.get('token_type') is not None}
        )
    
    return G
