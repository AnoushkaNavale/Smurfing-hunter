"""
FastAPI backend for the Smurfing-hunter pipeline.
"""

import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import sys

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT / "frontend"
OUTPUT_DIR = ROOT / "output"

sys.path.append(str(ROOT / "src"))

from data_loader import load_transactions
from graph_builder import build_transaction_graph
from report_generator import generate_report
from scoring_engine import compute_wallet_scores
from subgraph_extractor import extract_suspicious_subgraph
from visualization import visualize_laundering_graph


DEFAULT_ILLICIT_SEEDS = ["0xABC", "0xDEF"]


app = FastAPI(title="Smurfing-hunter API")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/runs/{run_id}/graph")
def get_graph(run_id: str):
    graph_file = OUTPUT_DIR / f"laundering_graph_{run_id}.html"
    if not graph_file.exists():
        raise HTTPException(status_code=404, detail="Graph not found")
    return FileResponse(graph_file)


@app.get("/api/runs/{run_id}/report")
def get_report(run_id: str):
    report_file = OUTPUT_DIR / f"suspicion_report_{run_id}.csv"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report_file, media_type="text/csv")


def _load_transactions_from_upload(upload: UploadFile) -> pd.DataFrame:
    upload.file.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        shutil.copyfileobj(upload.file, temp_file)
        temp_path = temp_file.name
    try:
        return load_transactions(temp_path)
    finally:
        os.remove(temp_path)


def _load_illicit_seeds_from_upload(upload: UploadFile) -> list[str]:
    upload.file.seek(0)
    df = pd.read_csv(upload.file)
    for column in ("Wallet_ID", "wallet_id", "wallet", "address"):
        if column in df.columns:
            seeds = df[column].dropna().astype(str).unique().tolist()
            if seeds:
                return seeds
    return []


def _fallback_subgraph(G, wallet_scores, max_nodes=200):
    top_nodes = sorted(
        wallet_scores.items(),
        key=lambda item: item[1].get("total", 0),
        reverse=True,
    )[:max_nodes]
    nodes = [wallet for wallet, _ in top_nodes]
    return G.subgraph(nodes).copy()


@app.post("/api/analyze")
async def analyze(
    transactions: UploadFile = File(...),
    illicit_wallets: UploadFile | None = File(None),
):
    if not transactions.filename:
        raise HTTPException(status_code=400, detail="Transactions file is required")

    df = _load_transactions_from_upload(transactions)
    if df.empty:
        raise HTTPException(status_code=400, detail="Transactions file is empty")

    seeds = DEFAULT_ILLICIT_SEEDS
    if illicit_wallets is not None and illicit_wallets.filename:
        seeds = _load_illicit_seeds_from_upload(illicit_wallets) or DEFAULT_ILLICIT_SEEDS

    G = build_transaction_graph(df)
    wallet_scores = compute_wallet_scores(G, seeds)
    subgraph = extract_suspicious_subgraph(G, seeds, wallet_scores)

    if subgraph.number_of_nodes() == 0:
        subgraph = _fallback_subgraph(G, wallet_scores)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex[:8]
    graph_file = OUTPUT_DIR / f"laundering_graph_{run_id}.html"
    report_file = OUTPUT_DIR / f"suspicion_report_{run_id}.csv"

    visualize_laundering_graph(
        subgraph,
        wallet_scores,
        seeds,
        str(graph_file),
        open_browser=False,
    )

    report = generate_report(wallet_scores, seeds)
    report.to_csv(report_file, index=False)
    report_preview = report.head(50)

    payload = {
        "run_id": run_id,
        "graph_url": f"/api/runs/{run_id}/graph",
        "report_url": f"/api/runs/{run_id}/report",
        "report": report_preview.to_dict(orient="records"),
        "report_count": len(report),
        "stats": {
            "transactions": len(df),
            "wallets": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "subgraph_nodes": subgraph.number_of_nodes(),
            "subgraph_edges": subgraph.number_of_edges(),
            "illicit_seeds": len(seeds),
        },
    }

    return JSONResponse(payload)
