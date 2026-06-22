import os
import json
from dotenv import load_dotenv
import anthropic
from menu import format_menu_for_prompt

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def route_intent(user_input, menu):
    menu_text = format_menu_for_prompt(menu)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system="""You are a phone menu routing assistant. Given a user's description of their problem and a phone menu, determine the best route.

Respond ONLY with a JSON object in this exact format:
{
    "primary_route": "option number and label",
    "secondary_route": "option number and label or null if not applicable",
    "reasoning": "one sentence explanation",
    "confidence": "high, medium, or low"
}

Rules:
- primary_route is always the best match
- secondary_route is only used when the problem spans two categories
- confidence is low when nothing matches well — suggest option 6 in that case
- Never invent options that don't exist in the menu""",
        messages=[
            {"role": "user", "content": f"Menu:\n{menu_text}\n\nUser's problem: {user_input}"}
        ]
    )

    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    cost = (input_tokens / 1_000_000) * 3.00 + (output_tokens / 1_000_000) * 15.00

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()


    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "primary_route": "6. Speak with a Representative",
            "secondary_route": None,
            "reasoning": "Could not parse routing decision — defaulting to representative",
            "confidence": "low"
        }

    return result, cost

def generate_clarifying_question(user_input, menu, initial_result):
    menu_text = format_menu_for_prompt(menu)
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        system="""You are a phone routing assistant. A user described their problem but the routing confidence is not high.
Generate ONE short, specific clarifying question that would help determine the correct phone menu option.
Return only the question — no explanation, no preamble.""",
        messages=[{"role": "user", "content": f"Menu:\n{menu_text}\n\nUser's problem: {user_input}\n\nInitial routing: {initial_result['primary_route']}\nReasoning: {initial_result['reasoning']}\n\nWhat single question would best clarify which option is correct?"}]
    )
    return message.content[0].text.strip()

def route_with_clarification(user_input, clarifying_question, user_answer, menu):
    menu_text = format_menu_for_prompt(menu)
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system="""You are a phone menu routing assistant. Given a user's description, a clarifying question that was asked, their answer, and a phone menu, determine the best route.

Respond ONLY with a JSON object in this exact format:
{
    "primary_route": "option number and label",
    "secondary_route": "option number and label or null if not applicable",
    "reasoning": "one sentence explanation",
    "confidence": "high, medium, or low"
}

Rules:
- primary_route is always the best match
- secondary_route is only used when the problem spans two categories
- confidence is low when nothing matches well — suggest option 6 in that case
- Never invent options that don't exist in the menu""",
        messages=[{"role": "user", "content": f"Menu:\n{menu_text}\n\nUser's original problem: {user_input}\nClarifying question asked: {clarifying_question}\nUser's answer: {user_answer}"}]
    )
    
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    cost = (input_tokens / 1_000_000) * 3.00 + (output_tokens / 1_000_000) * 15.00
    
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "primary_route": "6. Speak with a Representative",
            "secondary_route": None,
            "reasoning": "Could not parse routing decision — defaulting to representative",
            "confidence": "low"
        }
    
    return result, cost