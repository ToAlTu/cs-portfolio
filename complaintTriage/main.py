"""
main.py — command-line entry point for the complaint triage demo.

This file only ORCHESTRATES. The real work lives in the other modules:
    config.py      - settings, taxonomy, pricing
    prompts/       - the v1 and v2 system prompts
    classifier.py  - the engine (call Claude, parse, gate, cost)
    cfpb_api.py    - optional live data from the CFPB

Usage:
    python main.py                       # V1 vs V2 on the 3 clear sample cases
    python main.py --handoff             # also include the ambiguous handoff case
    python main.py --version v2          # run only the refined prompt
    python main.py --live "identity theft"   # pull real complaints from the CFPB
"""

import argparse
import json

import config
import classifier
import cfpb_api

VERSION_LABELS = {"v1": "V1  (naive: no severity definitions)",
                  "v2": "V2  (refined: defined severity + confidence)"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_samples(include_extended):
    """Load the offline sample complaints; drop the extended cases unless asked."""
    records = json.loads(config.DATA_FILE.read_text(encoding="utf-8"))
    if not include_extended:
        records = [r for r in records if r.get("tier", "core") == "core"]
    return records


def load_live(search_term):
    """Try the live CFPB fetch. Return records, or None to signal fallback."""
    try:
        records = cfpb_api.fetch_live(search_term)
    except Exception as err:  # noqa: BLE001 - demo must never crash on fetch
        print(f"  [live fetch failed: {err}]  Falling back to samples.\n")
        return None
    if not records:
        print("  [CFPB returned no narratives]  Falling back to samples.\n")
        return None
    return records


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def banner(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def show(result):
    """Print one triage decision, then its token/cost line."""
    if "_parse_error" in result:
        print(f"    !! could not parse model output: {result['_parse_error']}")
    else:
        # Product line, with a marker if the category isn't in the taxonomy.
        valid = result.get("category_valid")
        mark = "" if valid is None else ("  [valid]" if valid else "  [INVALID - not a CFPB category]")
        print(f"    product    : {result.get('product', '?')}{mark}")
        print(f"    issue      : {result.get('issue', '?')}")

        if "priority" in result:
            print(f"    priority   : {result.get('priority')}  (1=urgent ... 4=low)")
        if "severity" in result:  # v1 still uses this
            print(f"    severity   : {result.get('severity')}")

        flags = []
        if result.get("regulatory_flag"):
            flags.append("REGULATORY")
        if result.get("vulnerability_flag"):
            flags.append("VULNERABILITY")
        if flags:
            print(f"    flags      : {', '.join(flags)}")

        if "confidence" in result:
            print(f"    confidence : {result.get('confidence')}")
        if "rationale" in result:
            print(f"    why        : {result.get('rationale')}")
        if "recommended_action" in result:
            print(f"    suggested  : {result.get('recommended_action')}  (non-binding)")

        print(f"    routing    : {result.get('routing_team', result.get('routing', '?'))}")

        # The two independent human-in-the-loop signals.
        signals = []
        if result.get("escalate_to_human"):
            signals.append("HOLD FOR HUMAN (low confidence)")
        if result.get("needs_compliance_review"):
            signals.append("-> COMPLIANCE REVIEW (regulatory flag)")
        for s in signals:
            print(f"    >> {s}")

    usage = result.get("_usage")
    if usage:
        cost = usage.get("cost_usd")
        cost_str = f"${cost:.6f}" if cost is not None else "n/a"
        print(f"    [tokens: {usage['input_tokens']} in / "
              f"{usage['output_tokens']} out  |  cost: {cost_str}]")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run(client, complaints, versions):
    session_cost = 0.0
    cases = []
    for complaint in complaints:
        label = complaint["id"]
        if complaint.get("cfpb_product"):  # live records carry ground-truth labels
            label += (f"   [CFPB label: {complaint['cfpb_product']} / "
                      f"{complaint.get('cfpb_issue', '?')}]")
        banner(f"COMPLAINT: {label}")
        print(complaint["text"])

        case = {"id": complaint["id"], "text": complaint["text"]}
        for version in versions:
            print(f"\n  --- {VERSION_LABELS[version]} ---")
            result = classifier.triage(client, complaint["text"], version=version)
            show(result)
            case[version] = result
            usage = result.get("_usage") or {}
            if usage.get("cost_usd"):
                session_cost += usage["cost_usd"]
        cases.append(case)

    print("\n" + "-" * 72)
    print(f"Session total cost: ${session_cost:.6f}   (model: {config.MODEL})")
    print("Notes: same model + code -- only the PROMPT differs between V1 and V2.")
    print("-" * 72)
    return cases, session_cost


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CFPB complaint triage demo.")
    parser.add_argument("--version", choices=["v1", "v2", "both"], default="both",
                        help="which prompt version(s) to run (default: both)")
    parser.add_argument("--handoff", action="store_true",
                        help="include the ambiguous low-confidence handoff case")
    parser.add_argument("--live", metavar="SEARCH_TERM",
                        help="pull real complaints from the CFPB API by keyword")
    parser.add_argument("--save", action="store_true",
                        help="write triage_results.json for the HTML report")
    args = parser.parse_args()

    versions = ["v1", "v2"] if args.version == "both" else [args.version]

    complaints = None
    if args.live:
        banner(f"Pulling live CFPB complaints for: '{args.live}'")
        complaints = load_live(args.live)
    if complaints is None:
        # Fallback or default path. Include the handoff case if asked for it, or
        # if a live pull was attempted (so you still get a full set).
        complaints = load_samples(include_extended=args.handoff or bool(args.live))

    client = classifier.build_client()  # exits cleanly if the API key is missing
    cases, session_cost = run(client, complaints, versions)

    if args.save:
        out = config.BASE_DIR / "triage_results.json"
        out.write_text(json.dumps({
            "model": config.MODEL,
            "session_cost_usd": session_cost,
            "cases": cases,
        }, indent=2), encoding="utf-8")
        print(f"\nSaved -> {out.name}")


if __name__ == "__main__":
    main()