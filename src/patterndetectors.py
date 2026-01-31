"""
Pattern Detectors Module
Implements rule-based detection for fan-out, fan-in, peeling chains, and proximity scoring
"""

import networkx as nx
import numpy as np


def detect_fan_out(G, wallet, time_window_hours=1, min_degree=5, amount_similarity=0.15):
    """
    Detect fan-out pattern: one wallet sends to many within short time
    
    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        time_window_hours: Time window for concurrent transactions
        min_degree: Minimum number of recipients to flag
        amount_similarity: Maximum relative difference for similar amounts
        
    Returns:
        Count of suspicious fan-out events (capped at 10)
    """
    if wallet not in G:
        return 0
    
    out_edges = list(G.out_edges(wallet, data=True))
    if len(out_edges) < min_degree:
        return 0
    
    fan_out_count = 0
    
    for edge_data in out_edges:
        src, dst, data = edge_data
        timestamps = data['timestamps']
        amounts = data['amounts']
        
        for i, ts in enumerate(timestamps):
            concurrent_txs = []
            
            for other_edge in out_edges:
                _, other_dst, other_data = other_edge
                if other_dst == dst:
                    continue
                
                for j, other_ts in enumerate(other_data['timestamps']):
                    time_diff = abs((other_ts - ts).total_seconds() / 3600)
                    if time_diff <= time_window_hours:
                        concurrent_txs.append({
                            'dst': other_dst,
                            'amount': other_data['amounts'][j],
                            'timestamp': other_ts
                        })
            
            if len(concurrent_txs) >= min_degree - 1:
                all_amounts = [amounts[i]] + [tx['amount'] for tx in concurrent_txs]
                avg_amount = np.mean(all_amounts)
                
                similar_amounts = sum(
                    1 for amt in all_amounts 
                    if abs(amt - avg_amount) / avg_amount <= amount_similarity
                )
                
                if similar_amounts >= min_degree * 0.7:
                    fan_out_count += 1
                    break
    
    return min(fan_out_count, 10)


def detect_fan_in(G, wallet, min_degree=5, ancestor_depth=2):
    """
    Detect fan-in pattern: many wallets send to one (aggregation)
    Check if senders share common ancestors
    
    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        min_degree: Minimum number of senders to flag
        ancestor_depth: How far back to look for common ancestors
        
    Returns:
        Fan-in suspicion score (capped at 10)
    """
    if wallet not in G:
        return 0
    
    in_edges = list(G.in_edges(wallet, data=True))
    if len(in_edges) < min_degree:
        return 0
    
    senders = [src for src, dst, _ in in_edges]
    
    common_ancestor_pairs = 0
    
    for i, sender1 in enumerate(senders):
        ancestors1 = set()
        try:
            for depth in range(1, ancestor_depth + 1):
                for node in nx.single_source_shortest_path_length(
                    G.reverse(), sender1, cutoff=depth
                ).keys():
                    if node != sender1:
                        ancestors1.add(node)
        except:
            pass
        
        for sender2 in senders[i+1:]:
            ancestors2 = set()
            try:
                for depth in range(1, ancestor_depth + 1):
                    for node in nx.single_source_shortest_path_length(
                        G.reverse(), sender2, cutoff=depth
                    ).keys():
                        if node != sender2:
                            ancestors2.add(node)
            except:
                pass
            
            if len(ancestors1 & ancestors2) > 0:
                common_ancestor_pairs += 1
    
    expected_random = len(senders) * (len(senders) - 1) / 4 / G.number_of_nodes()
    
    if common_ancestor_pairs > expected_random * 2:
        return min(int(common_ancestor_pairs / 2), 10)
    
    return 0


def detect_gather_scatter(G, wallet, min_fan_out=3, min_recombine=2):
    """
    Detect gather-scatter (fan-out then fan-in) patterns.

    Pattern example: A -> {B,C,D} -> {F,G,H} -> Z

    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        min_fan_out: Minimum out-degree to consider scatter
        min_recombine: Minimum fan-in count to consider gather

    Returns:
        Count of gather-scatter structures (capped at 10)
    """
    if wallet not in G:
        return 0

    source_hits = 0
    intermediates = list(G.successors(wallet))
    if len(intermediates) >= min_fan_out:
        dest_counts = {}
        for node in intermediates:
            for dest in G.successors(node):
                if dest == wallet:
                    continue
                dest_counts[dest] = dest_counts.get(dest, 0) + 1

        source_hits = sum(1 for count in dest_counts.values() if count >= min_recombine)

    sink_hits = 0
    predecessors = list(G.predecessors(wallet))
    if len(predecessors) >= min_recombine:
        ancestor_counts = {}
        for node in predecessors:
            for ancestor in G.predecessors(node):
                if ancestor == wallet:
                    continue
                ancestor_counts[ancestor] = ancestor_counts.get(ancestor, 0) + 1

        sink_hits = sum(1 for count in ancestor_counts.values() if count >= min_fan_out)

    return min(source_hits + sink_hits, 10)


def detect_cyclic_patterns(G, wallet, max_cycle_length=6):
    """
    Detect cyclic laundering patterns that return to the same wallet.

    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        max_cycle_length: Max directed cycle length to consider

    Returns:
        Count of cyclic patterns (capped at 10)
    """
    if wallet not in G:
        return 0

    successors = list(G.successors(wallet))
    if not successors:
        return 0

    distances_to_wallet = nx.single_source_shortest_path_length(
        G.reverse(), wallet, cutoff=max_cycle_length - 1
    )

    cycle_hits = sum(1 for node in successors if node in distances_to_wallet)
    return min(cycle_hits, 10)


def detect_peeling_chains(
    G,
    wallet,
    min_length=4,
    min_peel_ratio=0.003,
    max_peel_ratio=0.05,
    min_delay_minutes=10,
    max_delay_hours=72,
    peel_time_window_minutes=60,
):
    """
    Detect peeling chains where small amounts are peeled off at each hop and
    time delays are introduced between hops to hide the trail.
    
    Args:
        G: NetworkX DiGraph
        wallet: Starting wallet address
        min_length: Minimum chain length to consider (nodes in the chain)
        min_peel_ratio: Minimum peel-to-main amount ratio per hop
        max_peel_ratio: Maximum peel-to-main amount ratio per hop
        min_delay_minutes: Minimum delay between main transfers
        max_delay_hours: Maximum delay between main transfers
        peel_time_window_minutes: Max time between peel tx and main tx
        
    Returns:
        Count of peeling chains detected (capped at 10)
    """
    if wallet not in G:
        return 0

    peeling_chains = 0
    min_delay_hours = min_delay_minutes / 60.0
    peel_window_seconds = peel_time_window_minutes * 60

    def edge_avg_amount(edge_data):
        count = edge_data.get("count", 0) or 1
        return edge_data.get("total_amount", 0) / count

    def select_edge_time(edge_data, after_time):
        timestamps = edge_data.get("timestamps", [])
        if not timestamps:
            return None
        sorted_times = sorted(timestamps)
        if after_time is None:
            return sorted_times[0]
        for ts in sorted_times:
            if ts > after_time:
                return ts
        return None

    def has_peel_edge(node, main_neighbor, main_amount, main_time):
        if main_amount <= 0:
            return False
        for peel_neighbor in G.successors(node):
            if peel_neighbor == main_neighbor:
                continue
            peel_data = G[node][peel_neighbor]
            peel_amount = edge_avg_amount(peel_data)
            ratio = peel_amount / main_amount
            if ratio < min_peel_ratio or ratio > max_peel_ratio:
                continue
            if main_time is None:
                return True
            for peel_time in peel_data.get("timestamps", []):
                if abs((peel_time - main_time).total_seconds()) <= peel_window_seconds:
                    return True
        return False

    def explore_path(current, path, amounts, times):
        nonlocal peeling_chains

        if len(path) >= min_length:
            is_decreasing = all(
                amounts[i] > amounts[i + 1] for i in range(len(amounts) - 1)
            )
            decay_rate = amounts[-1] / amounts[0] if amounts[0] > 0 else 0
            if is_decreasing and 0.5 <= decay_rate <= 0.98:
                peeling_chains += 1
                return

        if len(path) >= min_length + 2:
            return

        last_amount = amounts[-1] if amounts else None
        last_time = times[-1] if times else None

        for neighbor in G.successors(current):
            if neighbor in path:
                continue

            edge_data = G[current][neighbor]
            main_amount = edge_avg_amount(edge_data)
            if last_amount is not None and main_amount >= last_amount:
                continue

            main_time = select_edge_time(edge_data, last_time)
            if last_time is not None:
                if main_time is None:
                    continue
                delay_hours = (main_time - last_time).total_seconds() / 3600
                if delay_hours < min_delay_hours or delay_hours > max_delay_hours:
                    continue

            if not has_peel_edge(current, neighbor, main_amount, main_time):
                continue

            explore_path(
                neighbor,
                path + [neighbor],
                amounts + [main_amount],
                times + [main_time] if main_time else times,
            )

    explore_path(wallet, [wallet], [], [])

    return min(peeling_chains, 10)


def calculate_proximity_score(G, wallet, illicit_seeds, max_depth=3):
    """
    Calculate proximity to known illicit wallets
    Closer = higher score
    
    Args:
        G: NetworkX DiGraph
        wallet: Wallet address to analyze
        illicit_seeds: List of known illicit wallet addresses
        max_depth: Maximum hops to consider
        
    Returns:
        Proximity score (0-10, higher = closer to illicit wallets)
    """
    if wallet in illicit_seeds:
        return 10
    
    min_distance = float('inf')
    
    for seed in illicit_seeds:
        if seed not in G or wallet not in G:
            continue
        
        try:
            distance = nx.shortest_path_length(G, seed, wallet)
            min_distance = min(min_distance, distance)
        except nx.NetworkXNoPath:
            pass
        
        try:
            distance = nx.shortest_path_length(G, wallet, seed)
            min_distance = min(min_distance, distance)
        except nx.NetworkXNoPath:
            pass
    
    if min_distance == float('inf'):
        return 0
    
    if min_distance == 1:
        return 8
    elif min_distance == 2:
        return 5
    elif min_distance == 3:
        return 3
    else:
        return max(0, 10 - min_distance)