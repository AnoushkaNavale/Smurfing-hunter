---
title: Smurfing Hunter
emoji: 🕵️
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---
# Smurfing-hunter: GNN Money Laundering Detection

## Live Demo

Try the deployed app on Hugging Face Spaces:

[Smurfing-hunter Live Demo](https://huggingface.co/spaces/sncdwculbcw/smurfing-hunter)

A lightweight Graph Neural Network system for detecting suspicious wallets in
blockchain transaction graphs.

## Overview

This project analyzes blockchain transaction CSV files as wallet graphs. It uses
known illicit wallets as positive seed labels, builds transaction and neighborhood
features for every wallet, trains a two-layer Graph Convolutional Network, and
outputs a learned risk score for every wallet.

The GNN performs message passing over the transaction graph, so wallets can become
high risk when their own transaction behavior and their graph neighborhood resemble
known illicit seed regions.

## Project Structure

```text
main.py                 # CLI execution script
data_generator.py       # Synthetic blockchain data generator
backend/app.py          # FastAPI backend and frontend server
frontend/               # Browser UI
src/data_loader.py      # Transaction CSV loading
src/graph_builder.py    # Transaction graph construction
src/gnn_model.py        # NumPy-based Graph Neural Network
src/scoring_engine.py   # GNN wallet scoring interface
src/subgraph_extractor.py
src/visualization.py    # Interactive graph visualization
src/report_generator.py # Suspicion report generation
```

## Requirements

```text
pandas
networkx
pyvis
numpy
fastapi
uvicorn
python-multipart
```

## Input Data Format

The transaction CSV can use either schema.

Pipeline schema:

- `src_wallet`
- `dst_wallet`
- `amount`
- `timestamp`

Problem-statement schema:

- `Source_Wallet_ID`
- `Dest_Wallet_ID`
- `Timestamp`
- `Amount`
- `Token_Type` optional

Known illicit wallets can be supplied in a CSV with one of these columns:

- `Wallet_ID`
- `wallet_id`
- `wallet`
- `address`

## Usage

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the CLI pipeline:

```bash
python main.py
```

Start the web app:

```bash
python -m uvicorn backend.app:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## Outputs

The system generates:

- `output/laundering_graph.html`: interactive graph visualization
- `output/suspicion_report.csv`: all-wallet GNN risk report

Report columns include:

- `Wallet`
- `Score`
- `GNN_Probability`
- `GNN_Epochs`
- `GNN_Loss`
- `Explanation`
- `Is_Seed`

## GNN Method

The model is a two-layer Graph Convolutional Network implemented in NumPy. It:

1. Builds node features from transaction behavior.
2. Builds a normalized graph adjacency matrix with self-loops.
3. Uses illicit wallets as positive labels.
4. Uses unlabeled wallets as low-weight negative examples.
5. Trains with weighted binary cross-entropy.
6. Outputs a wallet risk probability from 0 to 1.

Node features include:

- incoming and outgoing degree
- incoming and outgoing transaction counts
- log-scaled incoming and outgoing volume
- max and average transfer amounts
- low-value incoming transaction ratio
- burstiness of incoming transactions
- unique sender and recipient counts
- token diversity
- known seed indicator

## Notes

- The model is intentionally lightweight and does not require PyTorch.
- The project uses NetworkX only to store and prepare the transaction graph; wallet
  risk scoring is performed by the GNN.
- This is a static batch-analysis system, not a real-time chain monitor.
