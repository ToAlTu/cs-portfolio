"""
report.py - render the demo into one clean, offline HTML page.

Reads the two saved result files and writes report.html. Makes NO API calls, so
it is safe to run (and re-open) any time, including in front of an interviewer.

Generate the inputs first:
    python main.py --handoff --save        ->  triage_results.json
    python evaluator.py --file "..." --save ->  eval_results.json

Then build the page:
    python report.py
    (open report.html in a browser)

The eval file is optional; if it's missing, the page renders the triage section
alone and notes that the scorecard wasn't generated.
"""

import json
import html
import datetime

import config

OUT = config.BASE_DIR / "report.html"
TRIAGE_FILE = config.BASE_DIR / "triage_results.json"
EVAL_FILE = config.BASE_DIR / "eval_results.json"

PRIORITY_LABEL = {1: "Urgent", 2: "Elevated", 3: "Standard", 4: "Low"}


def esc(x):
    return html.escape(str(x)) if x is not None else ""


# ---------------------------------------------------------------------------
# Eval section
# ---------------------------------------------------------------------------

def render_eval(ev):
    s = ev["summary"]
    n = s["n"] or 1

    def bar(value, total, kind):
        pct = round(100 * value / total) if total else 0
        return (f'<div class="bar-track">'
                f'<div class="bar-rail"><div class="bar-fill {kind}" style="--w:{pct}%"></div></div>'
                f'<div class="bar-num"><b>{pct}%</b> <span>{value}/{total}</span></div>'
                f'</div>')

    rows = []
    for i, r in enumerate(ev["rows"], 1):
        v1, v2 = r["v1"], r["v2"]
        rows.append(
            f'<tr><td class="num">{i}</td>'
            f'<td class="mono">{esc(r["ground_truth_bucket"])}</td>'
            f'<td class="mono muted">{esc(v1["bucket"])}</td>'
            f'<td class="{"hit" if v1["match"] else "miss"}">{"match" if v1["match"] else "—"}</td>'
            f'<td class="mono">{esc(v2["bucket"])}</td>'
            f'<td class="{"hit" if v2["match"] else "miss"}">{"match" if v2["match"] else "—"}</td>'
            f'</tr>')

    return f"""
    <section class="panel eval">
      <p class="eyebrow">Evaluation · scored against the CFPB's own product labels</p>
      <h2>The governed prompt, measured</h2>
      <p class="lede">Same model, same code &mdash; only the prompt differs. Two
      metrics, because they measure different things: whether the output is
      <em>routable</em>, and whether it's <em>right</em>.</p>

      <div class="metric">
        <div class="metric-head"><span class="metric-name">Conformance</span>
          <span class="metric-desc">produced a valid, routable CFPB category</span></div>
        <div class="metric-rows">
          <div class="metric-row"><span class="who">V1 naive</span>{bar(s['v1_valid'], n, 'v1')}</div>
          <div class="metric-row"><span class="who">V2 governed</span>{bar(s['v2_valid'], n, 'v2')}</div>
        </div>
      </div>

      <div class="metric">
        <div class="metric-head"><span class="metric-name">Understanding</span>
          <span class="metric-desc">matched the CFPB product (normalized, fair to V1's free text)</span></div>
        <div class="metric-rows">
          <div class="metric-row"><span class="who">V1 naive</span>{bar(s['v1_match'], n, 'v1')}</div>
          <div class="metric-row"><span class="who">V2 governed</span>{bar(s['v2_match'], n, 'v2')}</div>
        </div>
      </div>

      <details class="evidence">
        <summary>Per-case detail &middot; {n} complaints</summary>
        <table class="eval-table">
          <thead><tr><th>#</th><th>CFPB label</th><th>V1</th><th></th><th>V2</th><th></th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </details>

      <p class="caveat">CFPB product is consumer-selected at filing &mdash; a reasonable
      benchmark, not perfect truth; an occasional miss is the model being more right than the
      filer. Severity and priority are not scored (the CFPB publishes no urgency label).
      Sample drawn from <span class="mono">{esc(ev.get('source',''))}</span>.</p>
    </section>"""


# ---------------------------------------------------------------------------
# Triage section
# ---------------------------------------------------------------------------

def chip_priority(p):
    if p not in (1, 2, 3, 4):
        return ""
    return (f'<span class="chip prio p{p}">P{p} · {PRIORITY_LABEL[p]}</span>')


def flags_html(result):
    out = []
    if result.get("regulatory_flag"):
        out.append('<span class="flag reg">Regulatory</span>')
    if result.get("vulnerability_flag"):
        out.append('<span class="flag vuln">Vulnerability</span>')
    return "".join(out)


def signals_html(result):
    out = []
    if result.get("escalate_to_human"):
        out.append('<div class="signal hold">Hold for human · low confidence</div>')
    if result.get("needs_compliance_review"):
        out.append('<div class="signal comp">Route to compliance · regulatory flag</div>')
    return "".join(out)


def render_v1(v1):
    valid = v1.get("category_valid")
    prod = esc(v1.get("product"))
    prod_html = (f'<span class="cat bad">{prod}</span>' if valid is False
                 else f'<span class="cat">{prod}</span>')
    sev = v1.get("severity")
    sev_html = f'<span class="chip flat">{esc(sev)}</span>' if sev else ""
    return f"""
      <div class="col v1col">
        <div class="col-head">V1 <span>naive</span></div>
        <div class="field"><label>product</label>{prod_html}</div>
        <div class="field"><label>issue</label><p>{esc(v1.get('issue'))}</p></div>
        <div class="field"><label>severity</label>{sev_html or '<span class="muted">—</span>'}</div>
        <div class="field"><label>routing</label><span class="route bad">{esc(v1.get('routing_team'))}</span></div>
      </div>"""


def render_v2(v2):
    conf = v2.get("confidence")
    conf_html = f'<span class="conf">{conf}</span>' if conf is not None else ""
    return f"""
      <div class="col v2col">
        <div class="col-head">V2 <span>governed</span></div>
        <div class="field"><label>product</label><span class="cat ok">{esc(v2.get('product'))}</span></div>
        <div class="field"><label>issue</label><p>{esc(v2.get('issue'))}</p></div>
        <div class="field inline"><label>priority</label>{chip_priority(v2.get('priority'))}
          <label class="l2">flags</label>{flags_html(v2) or '<span class="muted">none</span>'}
          <label class="l2">conf</label>{conf_html}</div>
        <div class="field"><label>why</label><p class="why">{esc(v2.get('rationale'))}</p></div>
        <div class="field"><label>suggested</label><p class="sugg">{esc(v2.get('recommended_action'))}<span class="nb">non-binding</span></p></div>
        <div class="field"><label>routing</label><span class="route ok">{esc(v2.get('routing_team'))}</span></div>
        {signals_html(v2)}
      </div>"""


def render_case(case):
    v1 = case.get("v1", {})
    v2 = case.get("v2", {})
    return f"""
    <article class="case">
      <div class="case-head">
        <span class="case-id">{esc(case.get('id'))}</span>
        {chip_priority(v2.get('priority'))}
      </div>
      <p class="complaint">{esc(case.get('text'))}</p>
      <div class="diff">
        {render_v1(v1)}
        {render_v2(v2)}
      </div>
    </article>"""


def render_triage(tr):
    cases = "".join(render_case(c) for c in tr["cases"])
    return f"""
    <section class="panel triage">
      <p class="eyebrow">Live triage · five complaints, two prompts each</p>
      <h2>How each complaint is sorted</h2>
      <p class="lede">The naive prompt invents categories nothing can route. The
      governed prompt returns a real CFPB category, a priority, independent flags,
      a routable team, and &mdash; when it isn't sure &mdash; a hold for a human.</p>
      <div class="cases">{cases}</div>
    </section>"""


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------

def page(triage_html, eval_html, model, cost, source_note):
    today = datetime.date.today().isoformat()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Complaint Triage Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --paper:#E7EBEE; --surface:#FFFFFF; --ink:#13171D; --muted:#5E6976;
  --line:#D3DAE0; --line-soft:#E6EBEF;
  --accent:#15495A;
  --p1:#B23A2E; --p2:#B07320; --p3:#3F6C8E; --p4:#79858F;
  --reg:#5B43A0; --vuln:#1C7B68;
  --bad:#B23A2E; --bad-wash:#FAEEEC; --ok:#15495A;
  --hit:#1C7B68;
}}
* {{ box-sizing:border-box; }}
html {{ -webkit-text-size-adjust:100%; }}
body {{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:15px; line-height:1.55;
}}
.mono {{ font-family:"IBM Plex Mono",ui-monospace,monospace; }}
.wrap {{ max-width:1060px; margin:0 auto; padding:0 24px 80px; }}

/* Console header */
.masthead {{ border-bottom:1.5px solid var(--ink); padding:30px 0 16px; margin-bottom:34px; }}
.masthead .wrap {{ padding-bottom:0; padding-top:0; display:flex; flex-wrap:wrap;
  align-items:flex-end; justify-content:space-between; gap:14px; }}
.title {{ font-weight:700; font-size:26px; letter-spacing:-0.02em; line-height:1.05; }}
.title span {{ font-family:"IBM Plex Mono",monospace; font-weight:500; font-size:13px;
  letter-spacing:0.18em; text-transform:uppercase; color:var(--accent);
  display:block; margin-top:6px; }}
.runmeta {{ font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--muted);
  text-align:right; line-height:1.7; }}
.runmeta b {{ color:var(--ink); font-weight:600; }}

/* Panels */
.panel {{ margin-bottom:46px; }}
.eyebrow {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:0.14em;
  text-transform:uppercase; color:var(--accent); margin:0 0 10px; }}
h2 {{ font-size:27px; font-weight:700; letter-spacing:-0.02em; margin:0 0 10px; }}
.lede {{ color:var(--muted); max-width:60ch; margin:0 0 26px; }}
.lede em {{ color:var(--ink); font-style:normal; font-weight:600; }}

/* Eval metrics */
.metric {{ background:var(--surface); border:1px solid var(--line); border-radius:3px;
  padding:18px 20px; margin-bottom:14px; }}
.metric-head {{ display:flex; align-items:baseline; gap:12px; margin-bottom:14px;
  flex-wrap:wrap; }}
.metric-name {{ font-weight:600; font-size:16px; }}
.metric-desc {{ color:var(--muted); font-size:13px; }}
.metric-row {{ display:grid; grid-template-columns:96px 1fr; align-items:center;
  gap:14px; margin:7px 0; }}
.who {{ font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--muted); }}
.bar-track {{ display:grid; grid-template-columns:1fr 92px; align-items:center; gap:12px; }}
.bar-rail {{ height:24px; background:var(--line-soft); border-radius:2px; overflow:hidden; }}
.bar-fill {{ height:100%; width:var(--w); border-radius:2px 0 0 2px;
  animation:grow .9s cubic-bezier(.2,.7,.2,1) both; }}
.bar-fill.v1 {{ background:#A6B0B8; }}
.bar-fill.v2 {{ background:var(--accent); }}
.bar-num {{ font-family:"IBM Plex Mono",monospace; font-size:12px; white-space:nowrap; }}
.bar-num b {{ font-size:14px; font-weight:600; }}
.bar-num span {{ color:var(--muted); margin-left:3px; }}
@keyframes grow {{ from {{ width:0; }} to {{ width:var(--w); }} }}

.evidence {{ margin-top:6px; }}
.evidence summary {{ cursor:pointer; font-family:"IBM Plex Mono",monospace; font-size:12.5px;
  color:var(--accent); padding:6px 0; }}
.eval-table {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }}
.eval-table th {{ text-align:left; font-family:"IBM Plex Mono",monospace; font-weight:500;
  font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:var(--muted);
  border-bottom:1px solid var(--line); padding:7px 10px; }}
.eval-table td {{ padding:7px 10px; border-bottom:1px solid var(--line-soft); }}
.eval-table td.num {{ color:var(--muted); font-family:"IBM Plex Mono",monospace; }}
.eval-table td.mono {{ font-family:"IBM Plex Mono",monospace; font-size:12.5px; }}
.eval-table td.muted {{ color:var(--muted); }}
.hit {{ color:var(--hit); font-weight:600; font-size:12px; }}
.miss {{ color:var(--muted); }}

.caveat {{ font-size:12.5px; color:var(--muted); line-height:1.6; margin-top:20px;
  max-width:78ch; }}
.caveat .mono {{ font-size:11.5px; }}

/* Triage cases */
.case {{ background:var(--surface); border:1px solid var(--line); border-radius:3px;
  padding:0; margin-bottom:18px; overflow:hidden; }}
.case-head {{ display:flex; align-items:center; justify-content:space-between; gap:10px;
  padding:13px 18px; border-bottom:1px solid var(--line-soft); background:#FBFCFD; }}
.case-id {{ font-family:"IBM Plex Mono",monospace; font-size:12.5px; font-weight:600;
  letter-spacing:0.01em; }}
.complaint {{ margin:0; padding:15px 18px; color:#2C333B; font-size:14px;
  border-bottom:1px solid var(--line-soft); background:#fff; }}
.diff {{ display:grid; grid-template-columns:1fr 1.35fr; }}
.col {{ padding:16px 18px; }}
.v1col {{ background:var(--bad-wash); border-right:1px solid var(--line); }}
.v2col {{ background:#fff; }}
.col-head {{ font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:0.12em;
  text-transform:uppercase; color:var(--ink); font-weight:600; margin-bottom:14px; }}
.col-head span {{ color:var(--muted); font-weight:400; }}
.field {{ margin-bottom:11px; }}
.field label {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:10px;
  letter-spacing:0.1em; text-transform:uppercase; color:var(--muted); margin-bottom:3px; }}
.field.inline {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
.field.inline label {{ margin:0; }}
.field.inline label.l2 {{ margin-left:8px; }}
.field p {{ margin:0; font-size:13.5px; }}
.field p.why {{ color:#39414A; font-size:13px; line-height:1.5; }}
.field p.sugg {{ color:#39414A; font-size:13px; line-height:1.5; }}
.nb {{ display:inline-block; margin-left:7px; font-family:"IBM Plex Mono",monospace;
  font-size:10px; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted);
  border:1px solid var(--line); border-radius:2px; padding:1px 5px; vertical-align:middle; }}
.cat {{ font-family:"IBM Plex Mono",monospace; font-size:13px; font-weight:500; }}
.cat.ok {{ color:var(--ok); }}
.cat.bad {{ color:var(--bad); text-decoration:line-through; text-decoration-thickness:1px; }}
.conf {{ font-family:"IBM Plex Mono",monospace; font-weight:600; font-size:13px; }}
.route {{ font-family:"IBM Plex Mono",monospace; font-size:12.5px; font-weight:500; }}
.route.ok {{ color:var(--ink); }}
.route.bad {{ color:var(--bad); }}

.chip {{ display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:11px;
  font-weight:600; letter-spacing:0.02em; padding:3px 9px; border-radius:2px; color:#fff; }}
.chip.p1 {{ background:var(--p1); }} .chip.p2 {{ background:var(--p2); }}
.chip.p3 {{ background:var(--p3); }} .chip.p4 {{ background:var(--p4); }}
.chip.flat {{ background:#fff; color:var(--muted); border:1px solid var(--line); }}

.flag {{ display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:10.5px;
  font-weight:600; letter-spacing:0.04em; padding:2px 8px; border-radius:2px; }}
.flag.reg {{ color:var(--reg); background:#EFEBFA; }}
.flag.vuln {{ color:var(--vuln); background:#E5F4F0; }}

.signal {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; font-weight:500;
  padding:8px 11px; border-radius:2px; margin-top:10px; }}
.signal.hold {{ color:#fff; background:var(--p1); }}
.signal.comp {{ color:var(--reg); background:#EFEBFA; border:1px solid #DAD0F4; }}

.muted {{ color:var(--muted); }}

footer {{ border-top:1px solid var(--line); padding-top:18px; margin-top:10px;
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--muted); line-height:1.7; }}

@media (max-width:720px) {{
  .diff {{ grid-template-columns:1fr; }}
  .v1col {{ border-right:none; border-bottom:1px solid var(--line); }}
  .runmeta {{ text-align:left; }}
}}
@media (prefers-reduced-motion:reduce) {{
  .bar-fill {{ animation:none; }}
}}
</style>
</head>
<body>
<header class="masthead">
  <div class="wrap">
    <div class="title">Complaint Triage Console<span>CFPB · LLM-assisted routing</span></div>
    <div class="runmeta">
      model&nbsp; <b>{esc(model)}</b><br>
      {source_note}
      generated&nbsp; <b>{today}</b>
    </div>
  </div>
</header>
<main class="wrap">
  {eval_html}
  {triage_html}
  <footer>
    Classification is probabilistic; routing is deterministic (category &rarr; team, by config).
    A human makes the final decision &mdash; recommended actions are advisory.<br>
    Built on the Anthropic API · prompts and taxonomy are editable config, not code.
  </footer>
</main>
</body>
</html>"""


def main():
    if not TRIAGE_FILE.exists():
        raise SystemExit("triage_results.json not found. Run:  python main.py --handoff --save")

    tr = json.loads(TRIAGE_FILE.read_text(encoding="utf-8"))
    triage_html = render_triage(tr)
    model = tr.get("model", config.MODEL)
    cost = tr.get("session_cost_usd", 0)

    if EVAL_FILE.exists():
        ev = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
        eval_html = render_eval(ev)
        source_note = (f"triage&nbsp; <b>${cost:.4f}</b>&nbsp; · &nbsp;"
                       f"eval&nbsp; <b>${ev.get('cost_usd', 0):.4f}</b><br>")
    else:
        eval_html = ('<section class="panel"><p class="caveat">No '
                     'eval_results.json found &mdash; scorecard skipped. Run '
                     '<span class="mono">evaluator.py --file "..." --save</span> '
                     'to include it.</p></section>')
        source_note = f"triage&nbsp; <b>${cost:.4f}</b><br>"

    OUT.write_text(page(triage_html, eval_html, model, cost, source_note),
                   encoding="utf-8")
    print(f"Wrote {OUT.name}  ->  open it in a browser.")


if __name__ == "__main__":
    main()