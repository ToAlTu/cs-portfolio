"""
cfpb_api.py — pull real complaint narratives from the public CFPB database.

The CFPB Consumer Complaint Database has a free, no-key REST API. We use it to
fetch genuine consumer narratives on demand, so the demo can run on real data
instead of only the built-in samples.

Each returned record keeps the CFPB's own "product" and "issue" labels. Those are
ground truth: you can compare the model's classification against them in the room
("the model agreed with the CFPB's label here").

This module does no printing and no fallback logic of its own — if the network
call fails it raises, and the caller (main.py) decides whether to fall back to
samples. That keeps the data source and the app policy cleanly separate.
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

# The public search endpoint. No API key required.
BASE_URL = ("https://www.consumerfinance.gov/data-research/consumer-complaints/"
            "search/api/v1/")


def build_url(search_term, size=3):
    """Build the API request URL for a keyword search over complaint narratives."""
    params = {
        "search_term": search_term,
        "field": "complaint_what_happened",  # search the narrative text
        "has_narrative": "true",             # only complaints with a written story
        "size": str(size),
        "no_aggs": "true",                   # skip aggregation buckets we don't need
        "format": "json",
    }
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def _records_from_response(data):
    """Turn the raw CFPB JSON payload into our simple complaint records.

    Kept separate from the network call so it can be tested without internet.
    """
    hits = data.get("hits", {}).get("hits", [])
    records = []
    for i, hit in enumerate(hits, 1):
        src = hit.get("_source", {})
        narrative = (src.get("complaint_what_happened") or "").strip()
        if not narrative:
            continue
        records.append({
            "id": f"LIVE_{i}",
            "text": narrative,
            "cfpb_product": src.get("product"),  # ground-truth label
            "cfpb_issue": src.get("issue"),       # ground-truth label
        })
    return records


def fetch_live(search_term, size=3):
    """Fetch real complaint records for a keyword. May raise on network error.

    Returns a list of dicts shaped like the offline samples:
        {"id", "text", "cfpb_product", "cfpb_issue"}
    """
    url = build_url(search_term, size)
    # Some CFPB edge servers reject non-browser User-Agents with a 403, so we
    # present a browser-style one.
    headers = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0 Safari/537.36")}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _records_from_response(data)


def load_from_file(path, size=None):
    """Load complaint records from a downloaded CFPB JSON file.

    Accepts either the raw download (a list of {"_source": {...}} items) or the
    full API shape ({"hits": {"hits": [...]}}). Returns the same record shape as
    fetch_live, so the evaluator treats file and live data identically. This is
    the reliable, reproducible data source -- no network call, nothing to 403.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):  # full API response shape
        data = data.get("hits", {}).get("hits", [])

    records = []
    for item in data:
        src = item.get("_source", item)
        narrative = (src.get("complaint_what_happened") or "").strip()
        if not narrative:
            continue
        records.append({
            "id": str(src.get("complaint_id", len(records) + 1)),
            "text": narrative,
            "cfpb_product": src.get("product"),
            "cfpb_issue": src.get("issue"),
        })
        if size and len(records) >= size:
            break
    return records