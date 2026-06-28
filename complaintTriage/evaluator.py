"""
evaluator.py - measure the refinement, don't just claim it.

Runs V1 and V2 over real CFPB complaints (which carry the regulator's own
product label) and scores each version against that ground truth. Turns "I
improved the prompt" into "V2 matched the CFPB label on N of M; V1 on K of M."

Two metrics, on purpose:
  1. product_match  - did it pick the right product? Scored by normalizing BOTH
     prediction and ground truth into shared buckets, so V1's free-text answers
     get fair credit. Measures UNDERSTANDING.
  2. valid_category - did it output a category that exists in the controlled
     CFPB vocabulary (i.e. routable)? V1 invents labels and scores ~0 here.
     Measures CONFORMANCE.

Data source: a downloaded CFPB JSON file (--file, reliable/reproducible) or a
live API pull (--search). The file path is recommended for the demo.

Honest caveats, printed in the report:
  * CFPB product is consumer-selected at filing -- a reasonable benchmark, not
    perfect truth.
  * Severity/priority are NOT scored: the CFPB publishes no urgency label.

Slow (many sequential API calls) -- run BEFORE the interview. Use --save to
write eval_results.json for the HTML report.

Usage:
    python evaluator.py --file "C:\\path\\to\\complaints.json" --size 12 --save
    python evaluator.py --search "fee" --size 12
"""

import os
import argparse
import json

import config
import classifier
import cfpb_api


def canonical(text):
    """Map any product string (model output or CFPB label) to a shared bucket.

    Returns a category name, or None. Specific terms before generic ones. This
    absorbs V1's free-text phrasing and CFPB taxonomy drift over time.
    """
    if not text:
        return None
    t = text.strip().lower()

    names = {"credit_reporting", "debt_collection", "credit_card",
             "checking_savings", "money_transfer", "mortgage", "vehicle_loan",
             "student_loan", "personal_loan", "prepaid_card"}
    if t in names:
        return t
    if t == "other":
        return None

    if "prepaid" in t:
        return "prepaid_card"
    if "consumer report" in t or "credit report" in t or "reporting" in t:
        return "credit_reporting"
    if "debt" in t or "collection" in t:
        return "debt_collection"
    if "student loan" in t:
        return "student_loan"
    if "mortgage" in t:
        return "mortgage"
    if "vehicle" in t or "auto loan" in t or "car loan" in t or "lease" in t:
        return "vehicle_loan"
    if "payday" in t or "title loan" in t or "personal loan" in t or "advance loan" in t:
        return "personal_loan"
    if "money transfer" in t or "wire" in t or "virtual currency" in t \
            or "money service" in t or "remittance" in t:
        return "money_transfer"
    if "credit card" in t or "card" in t:
        return "credit_card"
    if "checking" in t or "saving" in t or "deposit" in t:
        return "checking_savings"
    return None


def ground_truth_buckets(text):
    """Acceptable bucket(s) for a CFPB ground-truth label.

    Most labels map to one bucket. Merged CFPB categories accept either, so a
    model that picks the more specific of the two is not unfairly marked wrong --
    e.g. 'Credit card or prepaid card' accepts credit_card OR prepaid_card.
    """
    if not text:
        return set()
    t = text.lower()
    if "credit card or prepaid card" in t:
        return {"credit_card", "prepaid_card"}
    b = canonical(text)
    return {b} if b else set()


def score(result, gt_buckets):
    """Score one version's result against the acceptable ground-truth bucket(s)."""
    raw = result.get("product") or ""
    pred_bucket = canonical(result.get("cfpb_product") or raw)
    return {
        "predicted": raw,
        "bucket": pred_bucket,
        "match": pred_bucket is not None and pred_bucket in gt_buckets,
        "valid_category": bool(result.get("category_valid")),
    }


def run_eval(client, records, source_label):
    """Run both versions over the records and score against ground truth."""
    rows, cost = [], 0.0
    for rec in records:
        gt_buckets = ground_truth_buckets(rec.get("cfpb_product"))
        if not gt_buckets:
            continue  # can't score fairly if we can't bucket the ground truth

        v1 = classifier.triage(client, rec["text"], version="v1")
        v2 = classifier.triage(client, rec["text"], version="v2")
        cost += (v1.get("_usage", {}).get("cost_usd") or 0)
        cost += (v2.get("_usage", {}).get("cost_usd") or 0)

        rows.append({
            "text": rec["text"],
            "ground_truth": rec.get("cfpb_product"),
            "ground_truth_bucket": "/".join(sorted(gt_buckets)),
            "v1": score(v1, gt_buckets),
            "v2": score(v2, gt_buckets),
        })

    n = len(rows)
    summary = {
        "n": n,
        "v1_match": sum(r["v1"]["match"] for r in rows),
        "v2_match": sum(r["v2"]["match"] for r in rows),
        "v1_valid": sum(r["v1"]["valid_category"] for r in rows),
        "v2_valid": sum(r["v2"]["valid_category"] for r in rows),
    }
    return {
        "source": source_label,
        "model": config.MODEL,
        "cost_usd": cost,
        "rows": rows,
        "summary": summary,
    }


def _pct(num, den):
    return f"{(100 * num / den):.0f}%" if den else "n/a"


def print_report(results):
    s = results["summary"]
    n = s["n"]
    print("\n" + "=" * 74)
    print("EVALUATION - V1 vs V2 product classification vs CFPB ground truth")
    print("=" * 74)
    print(f"{results['source']}  |  scored: {n}  |  model: {results['model']}")
    print()
    print(f"  {'#':>2}  {'ground truth':<18}  {'V1 bucket':<16} {'V1':<4} "
          f"{'V2 bucket':<16} {'V2':<4}")
    print("  " + "-" * 70)
    for i, r in enumerate(results["rows"], 1):
        v1m = "Y" if r["v1"]["match"] else "-"
        v2m = "Y" if r["v2"]["match"] else "-"
        print(f"  {i:>2}  {r['ground_truth_bucket']:<18}  "
              f"{str(r['v1']['bucket']):<16} {v1m:<4} "
              f"{str(r['v2']['bucket']):<16} {v2m:<4}")
    print()
    print("  Understanding  (product match, normalized -- fair to V1 free text):")
    print(f"     V1: {s['v1_match']}/{n} ({_pct(s['v1_match'], n)})     "
          f"V2: {s['v2_match']}/{n} ({_pct(s['v2_match'], n)})")
    print("  Conformance    (produced a valid CFPB category at all):")
    print(f"     V1: {s['v1_valid']}/{n} ({_pct(s['v1_valid'], n)})     "
          f"V2: {s['v2_valid']}/{n} ({_pct(s['v2_valid'], n)})")
    print()
    print(f"  cost: ${results['cost_usd']:.4f}")
    print("  note: CFPB product is consumer-selected (imperfect ground truth);")
    print("        severity/priority are not scored (no ground truth exists).")
    print("=" * 74)


def main():
    parser = argparse.ArgumentParser(description="Evaluate V1 vs V2 on CFPB data.")
    parser.add_argument("--file", help="path to a downloaded CFPB JSON file (recommended)")
    parser.add_argument("--search", default="fee",
                        help="CFPB keyword for a live pull (used if --file is absent)")
    parser.add_argument("--size", type=int, default=12,
                        help="how many complaints to evaluate (default: 12)")
    parser.add_argument("--save", action="store_true",
                        help="write eval_results.json for the HTML report")
    args = parser.parse_args()

    # Pick the data source: local file (reliable) or live API.
    if args.file:
        records = cfpb_api.load_from_file(args.file, size=args.size)
        source_label = f"file: {os.path.basename(args.file)}"
    else:
        try:
            records = cfpb_api.fetch_live(args.search, size=args.size)
        except Exception as err:  # noqa: BLE001
            raise SystemExit(f"Live fetch failed ({err}). Try --file instead.")
        source_label = f"search: '{args.search}'"

    if not records:
        raise SystemExit("No complaints loaded. Check the --file path or --search term.")

    client = classifier.build_client()
    print(f"Scoring V1 vs V2 over {len(records)} complaints "
          f"(~{len(records) * 2} API calls, please wait)...")
    results = run_eval(client, records, source_label)

    if results["summary"]["n"] == 0:
        raise SystemExit("No scorable complaints (couldn't bucket ground truth).")

    print_report(results)

    if args.save:
        out = config.BASE_DIR / "eval_results.json"
        out.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nSaved -> {out.name}")


if __name__ == "__main__":
    main()