"""
classifier.py - the triage engine.

Takes a complaint and a prompt version, returns a structured decision. It does
NO printing - it returns data, and the display layer decides how to show it.

What changed in the config-driven version:
  * The v2 prompt is RENDERED from triage_config.yaml (categories, severity
    rules, flags). The ops team edits the YAML; the wording lives in the prompt
    template. Two editable surfaces for two different roles.
  * The model returns a category NAME; this code validates it against the
    allowed list and looks up the routing team deterministically. The model
    never invents a destination.
  * Two independent human-in-the-loop signals: escalate_to_human (the model was
    unsure -> confidence gate) and needs_compliance_review (a regulated matter
    was flagged -> policy, regardless of confidence).

Pipeline:
    render prompt from config -> call Claude -> parse JSON
        -> validate category + look up route -> apply gates
        -> attach token/cost telemetry -> return dict
"""

import json
import os

import yaml
from anthropic import Anthropic
from dotenv import load_dotenv

import config

# Load the YAML once and reuse it.
_CONFIG = None


def load_config():
    """Load and cache the triage config (categories, rules, flags, routing)."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = yaml.safe_load(config.CONFIG_YAML.read_text(encoding="utf-8"))
    return _CONFIG


def build_client():
    """Create the Anthropic client, loading ANTHROPIC_API_KEY from .env."""
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY not found. Copy .env.example to .env and add your key."
        )
    return Anthropic()


# ---------------------------------------------------------------------------
# Prompt rendering (config -> prompt text)
# ---------------------------------------------------------------------------

def _render_categories(cfg):
    return "\n".join(f"- {c['name']}: {c['description'].strip()}"
                     for c in cfg["categories"])


def _render_severity_rules(cfg):
    lines = []
    for rule in cfg["severity_rules"]:
        if rule.get("default"):
            continue
        lines.append(f"- Priority {rule['priority']}: {rule['when'].strip()}")
    return "\n".join(lines)


def _render_flags(cfg):
    return "\n".join(f"- {name}: {desc.strip()}"
                     for name, desc in cfg["flags"].items())


def get_system_prompt(version, cfg):
    """Return the system prompt for a version. v1 is static; v2 is rendered."""
    if version == "v1":
        return (config.PROMPTS_DIR / "v1_system.txt").read_text(encoding="utf-8")
    template = (config.PROMPTS_DIR / "v2_system.txt").read_text(encoding="utf-8")
    return (template
            .replace("{categories}", _render_categories(cfg))
            .replace("{severity_rules}", _render_severity_rules(cfg))
            .replace("{flags}", _render_flags(cfg)))


# ---------------------------------------------------------------------------
# Output interpretation
# ---------------------------------------------------------------------------

def _extract_json(text):
    """Pull the JSON object out of the model's reply, tolerating code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[len("json"):]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model reply:\n{text}")
    return json.loads(text[start:end + 1])


def _resolve_category_and_route(result, cfg):
    """Validate the returned category and look up its team + ground-truth label.

    This is the 'interpret the output' step: we do NOT trust the model's product
    string blindly. If it isn't an allowed category name, it's unroutable -- which
    is exactly what a naive prompt that invents categories produces.
    """
    by_name = {c["name"]: c for c in cfg["categories"]}
    product = result.get("product")
    if product in by_name:
        result["category_valid"] = True
        result["cfpb_product"] = by_name[product]["cfpb_product"]
        result["routing_team"] = cfg["routing"].get(product, "Customer Relations")
    else:
        result["category_valid"] = False
        result["cfpb_product"] = None
        result["routing_team"] = "UNROUTABLE (category not in taxonomy)"
    return result


def _cost_usd(model, usage):
    rates = config.PRICING.get(model)
    if not rates:
        return None
    return (usage.input_tokens / 1_000_000) * rates["input"] + \
           (usage.output_tokens / 1_000_000) * rates["output"]


def triage(client, complaint_text, version="v2"):
    """Triage one complaint with the given prompt version. Returns a dict."""
    cfg = load_config()
    system_prompt = get_system_prompt(version, cfg)

    response = client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Complaint:\n{complaint_text}"}],
    )
    raw = "".join(block.text for block in response.content if block.type == "text")

    try:
        result = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as err:
        result = {"_parse_error": str(err), "_raw": raw}
        result["_usage"] = _usage_dict(response)
        return result

    # Interpret: validate category + deterministic routing.
    _resolve_category_and_route(result, cfg)

    # Two independent human-in-the-loop signals.
    conf = result.get("confidence")
    result["escalate_to_human"] = bool(
        isinstance(conf, (int, float)) and conf < config.CONFIDENCE_THRESHOLD
    )
    result["needs_compliance_review"] = bool(result.get("regulatory_flag"))

    result["_usage"] = _usage_dict(response)
    return result


def _usage_dict(response):
    return {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cost_usd": _cost_usd(config.MODEL, response.usage),
    }