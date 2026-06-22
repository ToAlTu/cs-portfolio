# Phone Menu Router

A command-line tool that takes a natural language description of a problem and routes it to the correct option in a phone menu tree using the Claude API. When confidence is low, it asks one clarifying question to improve routing accuracy.

## The problem it solves
Traditional phone menus require users to listen through all options and guess which one fits their problem. This tool lets users describe their problem naturally and get directed to the right option immediately — particularly useful when problems span multiple categories or don't fit neatly into any single option.

## How it works
1. The phone menu is defined as a structured set of options with descriptions
2. The user describes their problem in plain language
3. Claude reads both the menu and the problem, then returns a routing decision as structured JSON
4. If confidence is medium or low, the system generates one targeted clarifying question
5. The user's answer is used to re-route with higher confidence
6. The tool displays the primary route, an optional secondary route for complex problems, reasoning, and confidence level

## Example — ambiguous input resolved by clarification
```
Problem: "I need to pick up my prescription"

Initial routing: 1-2. Check refill status (medium confidence)

Clarifying question: Is your prescription already filled and waiting,
or do you need to request a refill first?

Answer: "It's already filled and waiting"

Final routing:
Primary:    1-2. Check refill status
Reasoning:  The user wants to confirm their prescription is ready for pickup
Confidence: high
```

## What we learned about confidence levels

**High confidence** — the user's problem maps cleanly to one menu option.

**Medium confidence (ambiguous input)** — the problem description could map to multiple options. One clarifying question typically resolves this to high confidence.

**Medium confidence (menu gap)** — the user's problem doesn't map well to any option because the menu doesn't cover that scenario. No amount of clarification fixes this — it reflects a gap in the menu itself, not the user's description. In these cases the system correctly routes to a representative or pharmacist.

This distinction is important: **the router's confidence reflects menu coverage, not just input quality.**

## Setup

1. Create a virtual environment and install dependencies:

```
pip install anthropic python-dotenv
```

2. Create a `.env` file in the project folder:

```
ANTHROPIC_API_KEY=your-key
```

3. Run the router:

```
python main.py
```

4. Describe your problem when prompted. Type `quit` to exit.

## Files

- `menu.py` — defines the phone menu structure and formatting utilities
- `router.py` — sends the menu and user input to Claude, returns structured JSON routing decisions, and generates clarifying questions
- `main.py` — handles user input, triggers clarification when needed, and displays results

## Notes
- Currently uses a hardcoded CVS Pharmacy menu
- Low or medium confidence automatically triggers one clarifying question
- Clarification is not repeated if confidence remains medium after one question
- Designed to be extended with configurable menus for any business type
