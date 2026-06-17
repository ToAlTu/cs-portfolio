# Resume Reviewer

A command-line tool that analyzes a resume PDF and provides direct, actionable feedback using the Claude API. Supports general and job-targeted review modes.

## How it works
1. Provide the path to your resume PDF
2. Choose general or targeted mode
3. For targeted mode, enter a job title or paste a job description
4. Claude returns structured feedback: issues to fix, quick wins, and general impression
5. Token usage and cost are displayed after each request

## Setup

1. Create a virtual environment and install dependencies:

```
pip install anthropic python-dotenv pymupdf
```

2. Create a `.env` file in the project folder:

```
ANTHROPIC_API_KEY=your-key
```

3. Run the reviewer:

```
python resume_reviewer.py
```

4. Enter the full path to your resume PDF when prompted

5. Choose your review mode:
   - **1. General** — universal feedback on structure, content, and presentation
   - **2. Targeted** — feedback tailored to a specific job, including skill gaps and fit analysis
