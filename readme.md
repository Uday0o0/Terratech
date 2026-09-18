# TerraTech

Predictive Analytics System for Early Detection of Land Acquisition Delays
Smart India Hackathon — Team TerraTech

## What this is
A 2-day proof-of-concept demonstrating an ML-driven approach to flagging
land acquisition projects at risk of delay, with explainability (SHAP)
and rule-based recommendations.

## What this is NOT
- Not a production government system
- Not built on real government data (synthetic/anonymized data only)
- No authentication, no database, no REST API — see docs/limitations.md

## Structure
- `notebook/` — ML exploration and model training (Jupyter)
- `data/` — synthetic historical dataset + demo project JSON
- `models/` — trained classifier + preprocessing artifacts
- `src/` — prediction, explainability, and recommendation logic
- `app.py` — Streamlit demo application
- `docs/` — architecture, ML methodology, limitations, demo script

## Setup
See below.