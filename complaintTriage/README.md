# Complaint Triage Assistant
 
An LLM-powered triage pipeline for U.S. consumer-finance complaints. A complaint arrives as free text; the system classifies it against the real CFPB product taxonomy, assigns a priority (1–4), raises independent regulatory and vulnerability flags, routes it to the correct team, and — when it isn't confident — holds the case for human review instead of guessing.
 
Built on the [Anthropic API](https://www.anthropic.com) using Claude. Prompts and taxonomy are editable config, not code — so the business rules can be retuned without touching the application.
 
---
 
## What it demonstrates
 
- **Prompt engineering** — a naive V1 prompt vs a governed V2 prompt rendered from a YAML config, showing the structural and measurable difference between them
- **Interpreting LLM output** — JSON validation, category conformance checking, and deterministic routing in application code rather than trusting the model to name a destination
- **Refining results** — an evaluator that scores V1 vs V2 against the CFPB's own ground-truth product labels on real complaint data
---
 
## Project structure
 
```
complaintTriage/
├── .env.example              # API key template (copy to .env)
├── .gitignore
├── requirements.txt
├── config.py                 # Model, threshold, pricing, file paths
├── triage_config.yaml        # CFPB taxonomy, priority rules, flags, routing
├── prompts/
│   ├── v1_system.txt         # Naive prompt — the "before"
│   ├── v2_system.txt         # Governed prompt — the "after"
│   └── v2_system_flat_fallback.txt
├── data/
│   └── sample_complaints.json
├── classifier.py             # Core engine: prompt rendering, API call, gating, cost
├── cfpb_api.py               # Live CFPB data fetch + local file loader
├── evaluator.py              # V1 vs V2 accuracy scoring against CFPB ground truth
├── main.py                   # CLI entry point
└── report.py                 # Renders triage_results.json + eval_results.json → report.html
```
 
---
 
## Setup
 
**1. Clone and create a virtual environment**
```bash
git clone https://github.com/ToAlTu/cs-portfolio.git
cd cs-portfolio/complaintTriage
python -m venv .venv
 
# Windows
.venv\Scripts\activate
 
# macOS / Linux
source .venv/bin/activate
```
 
**2. Install dependencies**
```bash
pip install -r requirements.txt
```
 
**3. Add your API key**
```bash
cp .env.example .env
# Open .env and paste your Anthropic API key
```
 
Get a key at [console.anthropic.com](https://console.anthropic.com).
 
---
 
## Running the demo
 
**Core demo — V1 vs V2 on three clear complaints**
```bash
python main.py
```
 
**Full demo — includes the two ambiguous cases (confidence hold + scam)**
```bash
python main.py --handoff
```
 
**Save results for the HTML report**
```bash
python main.py --handoff --save
```
 
**Pull live complaints from the CFPB public API**
```bash
python main.py --live "identity theft"
```
 
**Run only one prompt version**
```bash
python main.py --version v2
```
 
---
 
## Evaluator
 
Scores V1 vs V2 against real CFPB complaints which carry the regulator's own product label as ground truth. Two metrics: conformance (did it produce a routable CFPB category) and understanding (did it match the correct product, normalized fairly for V1's free-text output).
 
**From a downloaded CFPB JSON file (recommended — no network dependency)**
```bash
python evaluator.py --file "path/to/complaints.json" --size 12 --save
```
 
**From a live API pull**
```bash
python evaluator.py --search "fee" --size 12 --save
```
 
Download real complaint data at [consumerfinance.gov/data-research/consumer-complaints](https://www.consumerfinance.gov/data-research/consumer-complaints/).
 
---
 
## HTML report
 
Generates a self-contained offline report combining the triage results and the evaluation scorecard. No API calls at render time — safe to open in a browser anytime.
 
```bash
# Generate the data files first
python main.py --handoff --save
python evaluator.py --file "path/to/complaints.json" --size 12 --save
 
# Render the report
python report.py
# Opens: report.html
```
 
---
 
## How it works
 
### The pipeline
 
```
Free-text complaint
    → Render system prompt from triage_config.yaml
    → Call Claude API
    → Parse + validate JSON response
    → Check category against CFPB taxonomy
    → Look up routing team deterministically (config map, not the model)
    → Apply confidence gate (< 0.70 → hold for human)
    → Apply regulatory gate (regulatory_flag → compliance review)
    → Output decision + token cost
```
 
### Key design decisions
 
**Classification is probabilistic; routing is deterministic.** The model picks a category name from a constrained list. The application code looks up the team from a config map. The model can never invent a destination.
 
**Two independent human-in-the-loop signals.** A confidence gate escalates when the model is unsure. A regulatory gate routes to compliance whenever a potential statute violation is flagged — regardless of confidence. A complaint can trip both, either, or neither.
 
**Prompts are rendered from config, not hard-coded.** The YAML holds the taxonomy, severity rules, and routing. The prompt template holds the wording. Engineers own the template; the ops/compliance team owns the YAML. Neither needs to touch the other's file to make a change.
 
---
 
## Sample output
 
```
COMPLAINT: A_high_identity_theft
I discovered an account with XXXX XXXX that I never opened...
 
  --- V1  (naive: no severity definitions) ---
    product    : Credit Card  [INVALID - not a CFPB category]
    routing    : UNROUTABLE (category not in taxonomy)
    [tokens: 166 in / 51 out  |  cost: $0.001263]
 
  --- V2  (refined: defined severity + confidence) ---
    product    : credit_card  [valid]
    priority   : 1  (1=urgent ... 4=low)
    flags      : REGULATORY
    confidence : 0.88
    why        : Active identity theft with unauthorized account impacting credit report...
    suggested  : Verify identity, initiate fraud protocol, coordinate credit dispute...  (non-binding)
    routing    : Card Services
    >> -> COMPLIANCE REVIEW (regulatory flag)
    [tokens: 991 in / 228 out  |  cost: $0.006393]
```
 
---
 
## Evaluation results
 
Scored on 12 real CFPB complaints against the regulator's own product labels.
 
| Metric | V1 naive | V2 governed |
|---|---|---|
| Conformance (routable category) | 0 / 12 — 0% | 12 / 12 — 100% |
| Understanding (correct product) | 7 / 12 — 58% | 9 / 12 — 75% |
 
Same model, same code — only the prompt changed.
 
> CFPB product is consumer-selected at filing — a reasonable benchmark, not perfect truth. Severity and priority are not scored (the CFPB publishes no urgency label).
 
---
 
## Production considerations
 
These are not implemented in the demo but are the natural next steps for production scale:
 
- **Batch API** — 50% cheaper; complaints aren't real-time so overnight batch processing fits well
- **Prompt caching** — ~90% input cost reduction on the static system prompt once it exceeds the caching threshold
- **Model tiering** — cheap model (Haiku) for the confident majority; escalate to a stronger model on low-confidence cases, which the confidence gate already identifies
- **Response drafting** — extend the pipeline to draft a first-pass response alongside the triage decision, always human-approved
---
 
## Data source
 
Complaint data comes from the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/), a public dataset maintained by the Consumer Financial Protection Bureau. Narratives are published with consumer consent after personal information is removed.