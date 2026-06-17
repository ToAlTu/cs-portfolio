# Text Summarizer

A command-line tool that summarizes any block of text into 3 clear bullet points using the Claude API. Tracks token usage and cost per request.

## How it works
1. Run the script and paste any text
2. Type a blank line when finished
3. Claude summarizes it into 3 bullet points
4. Token usage and cost are displayed after each request

## Setup

1. Create a virtual environment and install dependencies:

```
pip install anthropic python-dotenv
```

2. Create a `.env` file in the project folder:

```
ANTHROPIC_API_KEY=your-key
```

3. Run the summarizer:

```
python summarizer.py
```
