"""
Flask backend for the product catalog + AI recommendation demo,
structured to run as a Vercel Serverless Function.

Vercel's Python runtime detects a WSGI-compatible `app` object in this
file and wraps it automatically — no extra handler code needed.

Endpoints (note the /api prefix matches this file's location):
  GET  /api/products
  POST /api/recommend
  GET  /api/health
"""

import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------------------------------------------------------------------------
# Product catalog
# ---------------------------------------------------------------------------
PRODUCTS = [
    {"id": "p1", "name": "Apple iPhone 15", "category": "Phones", "price": 799, "meta": "6.1in - 128GB - 5G"},
    {"id": "p2", "name": "Samsung Galaxy S24 Ultra", "category": "Phones", "price": 1299, "meta": "6.8in - 256GB - 5G"},
    {"id": "p3", "name": "Google Pixel 8a", "category": "Phones", "price": 499, "meta": "6.1in - 128GB - 5G"},
    {"id": "p4", "name": "OnePlus 12", "category": "Phones", "price": 799, "meta": "6.82in - 256GB - 5G"},
    {"id": "p5", "name": "Apple MacBook Air M3", "category": "Laptops", "price": 1099, "meta": "13.6in - 16GB RAM - 512GB SSD"},
    {"id": "p6", "name": "Dell XPS 13", "category": "Laptops", "price": 999, "meta": "13.4in - 16GB RAM - 512GB SSD"},
    {"id": "p7", "name": "Lenovo ThinkPad X1 Carbon Gen 12", "category": "Laptops", "price": 1799, "meta": "14in - 32GB RAM - 1TB SSD"},
    {"id": "p8", "name": "Apple AirPods Pro (2nd Gen)", "category": "Audio", "price": 249, "meta": "Wireless - ANC - USB-C Charging"},
    {"id": "p9", "name": "Sony WH-1000XM5", "category": "Audio", "price": 399, "meta": "Wireless - ANC - 30h battery"},
    {"id": "p10", "name": "JBL Tune 230NC TWS", "category": "Audio", "price": 99, "meta": "Wireless - ANC - 40h battery"},
    {"id": "p11", "name": "Apple Watch SE (2nd Gen)", "category": "Wearables", "price": 249, "meta": "GPS - Heart Rate - Retina Display"},
    {"id": "p12", "name": "Samsung Galaxy Watch 7", "category": "Wearables", "price": 349, "meta": "GPS - ECG - Sleep Tracking"},
    {"id": "p13", "name": "Apple iPad Air 11-inch", "category": "Tablets", "price": 599, "meta": "11in - 128GB - Wi-Fi"},
    {"id": "p14", "name": "Samsung Galaxy Tab S9 FE 5G", "category": "Tablets", "price": 699, "meta": "10.9in - 128GB - 5G"},
    {"id": "p15", "name": "Keychron K8 Pro", "category": "Accessories", "price": 99, "meta": "Mechanical - Wireless - Hot-swappable"},
    {"id": "p16", "name": "Logitech MX Master 3S", "category": "Accessories", "price": 99, "meta": "Wireless - Ergonomic - Multi-device"},
]

PRODUCTS_BY_ID = {p["id"]: p for p in PRODUCTS}


def build_catalog_text(products):
    return "\n".join(
        f"{p['id']} | {p['name']} | {p['category']} | ${p['price']} | {p['meta']}"
        for p in products
    )


def call_openai_for_recommendations(query: str) -> dict:
    system_prompt = (
        "You are a product recommendation engine for an electronics store.\n"
        "You will be given a catalog of products (id | name | category | price | spec) "
        "and a shopper's request.\n"
        "Pick the best-matching products (usually 1-3, never more than 4) from the "
        "catalog ONLY - never invent products.\n"
        "Respond with ONLY valid JSON, no markdown fences, no preamble, in exactly "
        "this shape:\n"
        '{"picks": [{"id": "p1", "reason": "one short clause, under 16 words, on why this fits"}], '
        '"note": "one short sentence summarizing your overall reasoning"}\n'
        "If nothing in the catalog reasonably fits, return "
        '{"picks": [], "note": "explain briefly why nothing fits"}.'
    )
    user_prompt = f"Catalog:\n{build_catalog_text(PRODUCTS)}\n\nShopper request: \"{query}\""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content or ""
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(PRODUCTS)


@app.route("/api/recommend", methods=["POST"])
def recommend():
    if client is None:
        return jsonify({
            "error": "Server is missing OPENAI_API_KEY. Add it in Vercel Project Settings > Environment Variables, then redeploy."
        }), 500

    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Request body must include a non-empty 'query' string."}), 400

    try:
        result = call_openai_for_recommendations(query)
    except json.JSONDecodeError:
        return jsonify({"error": "The AI returned a response that could not be parsed. Try rephrasing."}), 502
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"OpenAI request failed: {exc}"}), 502

    picks = result.get("picks", [])
    enriched_picks = []
    for pick in picks:
        product = PRODUCTS_BY_ID.get(pick.get("id"))
        if product:
            enriched_picks.append({**product, "reason": pick.get("reason", "")})

    return jsonify({"picks": enriched_picks, "note": result.get("note", "")})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "openai_configured": client is not None})


# Vercel's Python runtime looks for a WSGI-compatible `app` object at module
# level - having `app = Flask(__name__)` above is all that's required.
# No `if __name__ == "__main__"` block is needed for deployment, but it's
# kept here so you can still run this file locally with `python api/index.py`.
if __name__ == "__main__":
    app.run(debug=True, port=5000)
