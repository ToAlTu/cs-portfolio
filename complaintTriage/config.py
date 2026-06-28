"""
Central configuration for the complaint triage app.
 
Everything tunable lives here so the rest of the code never hard-codes a model
name, a threshold, or a category. Change it once, it changes everywhere.
"""
 
from pathlib import Path
 
# --- Model -----------------------------------------------------------------
# Sonnet 4.6 gives the better-calibrated reasoning the ambiguous cases need.
# For production-scale volume, "claude-haiku-4-5" is cheaper and faster -- a
# deliberate cost/quality trade-off worth mentioning out loud.
MODEL = "claude-sonnet-4-6"
 
# Max tokens for the model's reply. Triage output is small; this is plenty.
MAX_TOKENS = 600

# --- Pricing (USD per million tokens) --------------------------------------
# Used to print the cost of each API call. Keyed by model so the readout stays
# correct if MODEL changes above. Rates per Anthropic's pricing page.
PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5":  {"input": 1.00, "output": 5.00},
    "claude-opus-4-8":   {"input": 5.00, "output": 25.00},
}

# --- Human-in-the-loop gate ------------------------------------------------
# If the model's self-reported confidence falls below this, the case is routed
# to a human reviewer instead of being auto-actioned. This is the responsible-AI
# heart of the design: the app escalates uncertainty rather than guessing.
CONFIDENCE_THRESHOLD = 0.70

 
# --- File locations --------------------------------------------------------
# Resolved relative to this file so the app runs from any working directory.
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
DATA_FILE = BASE_DIR / "data" / "sample_complaints.json"
CONFIG_YAML = BASE_DIR / "triage_config.yaml"