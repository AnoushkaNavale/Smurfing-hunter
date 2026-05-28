"""
Lightweight Graph Neural Network for wallet risk scoring.

This module implements a small two-layer Graph Convolutional Network with NumPy.
It avoids heavyweight ML dependencies while still performing learned message
passing over the transaction graph.
"""

import math

import numpy as np


def _sigmoid(values):
    values = np.clip(values, -40, 40)
    return 1.0 / (1.0 + np.exp(-values))


def _relu(values):
    return np.maximum(values, 0)


def _build_node_features(G, nodes, illicit_seeds):
    seed_set = set(illicit_seeds)
    rows = []

    for node in nodes:
        in_edges = list(G.in_edges(node, data=True))
        out_edges = list(G.out_edges(node, data=True))

        incoming_amounts = []
        outgoing_amounts = []
        incoming_timestamps = []
        token_types = set()

        for _, _, data in in_edges:
            incoming_amounts.extend(data.get("amounts", []))
            incoming_timestamps.extend(data.get("timestamps", []))
            token_types.update(data.get("token_types", []))

        for _, _, data in out_edges:
            outgoing_amounts.extend(data.get("amounts", []))
            token_types.update(data.get("token_types", []))

        in_total = float(sum(incoming_amounts))
        out_total = float(sum(outgoing_amounts))
        in_count = len(incoming_amounts)
        out_count = len(outgoing_amounts)
        low_value_ratio = (
            sum(1 for amount in incoming_amounts if amount <= 100) / in_count
            if in_count
            else 0.0
        )

        sorted_times = sorted(incoming_timestamps)
        if len(sorted_times) > 1:
            intervals = [
                (sorted_times[index + 1] - sorted_times[index]).total_seconds()
                for index in range(len(sorted_times) - 1)
            ]
            burstiness = sum(1 for value in intervals if value <= 3600) / len(intervals)
        else:
            burstiness = 0.0

        rows.append(
            [
                len(in_edges),
                len(out_edges),
                in_count,
                out_count,
                math.log1p(in_total),
                math.log1p(out_total),
                math.log1p(max(incoming_amounts) if incoming_amounts else 0),
                math.log1p(max(outgoing_amounts) if outgoing_amounts else 0),
                math.log1p(in_total / in_count) if in_count else 0.0,
                math.log1p(out_total / out_count) if out_count else 0.0,
                low_value_ratio,
                burstiness,
                len({src for src, _, _ in in_edges}),
                len({dst for _, dst, _ in out_edges}),
                len(token_types),
                1.0 if node in seed_set else 0.0,
            ]
        )

    features = np.array(rows, dtype=np.float64)
    mean = features.mean(axis=0)
    std = features.std(axis=0)
    std[std == 0] = 1.0
    return (features - mean) / std


def _build_normalized_adjacency(G, nodes):
    node_index = {node: index for index, node in enumerate(nodes)}
    size = len(nodes)
    adjacency = np.eye(size, dtype=np.float64)

    for src, dst in G.edges():
        src_index = node_index[src]
        dst_index = node_index[dst]
        adjacency[src_index, dst_index] = 1.0
        adjacency[dst_index, src_index] = 1.0

    degrees = adjacency.sum(axis=1)
    degrees[degrees == 0] = 1.0
    degree_inv_sqrt = 1.0 / np.sqrt(degrees)
    return degree_inv_sqrt[:, None] * adjacency * degree_inv_sqrt[None, :]


def _training_labels(nodes, illicit_seeds):
    seed_set = set(illicit_seeds)
    labels = np.array([1.0 if node in seed_set else 0.0 for node in nodes])

    positive_count = labels.sum()
    negative_count = len(labels) - positive_count
    weights = np.full(len(labels), 0.12, dtype=np.float64)

    if positive_count:
        weights[labels == 1] = max(1.0, negative_count / positive_count)
    else:
        weights[:] = 1.0

    return labels, weights


def train_gnn_wallet_scorer(
    G,
    illicit_seeds,
    hidden_dim=24,
    epochs=450,
    learning_rate=0.035,
    seed=7,
):
    """
    Train a two-layer GCN and return per-wallet risk probabilities.
    """
    nodes = list(G.nodes())
    if not nodes:
        return {}, {"epochs": 0, "loss": 0.0}

    features = _build_node_features(G, nodes, illicit_seeds)
    adjacency = _build_normalized_adjacency(G, nodes)
    labels, sample_weights = _training_labels(nodes, illicit_seeds)

    rng = np.random.default_rng(seed)
    input_dim = features.shape[1]
    W0 = rng.normal(0, math.sqrt(2 / input_dim), size=(input_dim, hidden_dim))
    b0 = np.zeros(hidden_dim)
    W1 = rng.normal(0, math.sqrt(2 / hidden_dim), size=hidden_dim)
    b1 = 0.0

    AX = adjacency @ features
    weight_scale = sample_weights.sum()
    last_loss = 0.0

    for _ in range(epochs):
        Z1 = AX @ W0 + b0
        H = _relu(Z1)
        AH = adjacency @ H
        logits = AH @ W1 + b1
        probabilities = _sigmoid(logits)

        eps = 1e-9
        loss_terms = -(
            labels * np.log(probabilities + eps)
            + (1 - labels) * np.log(1 - probabilities + eps)
        )
        last_loss = float((loss_terms * sample_weights).sum() / weight_scale)

        dlogits = (probabilities - labels) * sample_weights / weight_scale
        grad_W1 = AH.T @ dlogits
        grad_b1 = float(dlogits.sum())

        dAH = dlogits[:, None] * W1[None, :]
        dH = adjacency.T @ dAH
        dZ1 = dH * (Z1 > 0)
        grad_W0 = AX.T @ dZ1
        grad_b0 = dZ1.sum(axis=0)

        W0 -= learning_rate * grad_W0
        b0 -= learning_rate * grad_b0
        W1 -= learning_rate * grad_W1
        b1 -= learning_rate * grad_b1

    Z1 = AX @ W0 + b0
    H = _relu(Z1)
    probabilities = _sigmoid((adjacency @ H) @ W1 + b1)

    seed_set = set(illicit_seeds)
    raw_scores = {}
    for node, probability in zip(nodes, probabilities):
        if node in seed_set:
            probability = max(float(probability), 0.99)
        raw_scores[node] = float(probability)

    metadata = {
        "epochs": epochs,
        "loss": round(last_loss, 4),
        "positive_labels": int(labels.sum()),
        "feature_count": input_dim,
        "hidden_dim": hidden_dim,
    }
    return raw_scores, metadata
