# Phone Menu Router

A command-line tool that takes a natural language description of a problem and routes it to the correct option in a phone menu tree using the Claude API.

## The problem it solves
Traditional phone menus require users to listen through all options and guess which one fits their problem. This tool lets users describe their problem naturally and get directed to the right option immediately — particularly useful when problems span multiple categories or don't fit neatly into any single option.

## How it works
1. The phone menu is defined as a structured set of options with descriptions
2. The user describes their problem in plain language
3. Claude reads both the menu and the problem, then returns a routing decision as structured JSON
4. The tool displays the primary route, an optional secondary route for complex problems, reasoning, and confidence level

## Example
```
Problem: "I need to refill my prescription but the doctor changed the dosage"

Primary:    1-1. Request a refill
Secondary:  4. Speak with a Pharmacist
Reasoning:  The dosage change adds complexity that may require pharmacist guidance
Confidence: medium
```

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
- `router.py` — sends the menu and user input to Claude, returns a structured routing decision
- `main.py` — handles user input and displays the routing result

## Notes
- Currently uses a hardcoded CVS Pharmacy menu
- Low confidence results automatically route to a live representative
- Designed to be extended with configurable menus for any business type
