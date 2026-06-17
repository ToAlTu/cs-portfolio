### Resume Reviewer
Reviews a resume PDF and provides direct, actionable feedback. Supports two modes:
- **General** — universal feedback on structure, content, and presentation
- **Targeted** — feedback tailored to a specific job title or description, including skill gaps and fit analysis

**How to run:**
1. Clone the repo
2. Create a `.env` file with your `ANTHROPIC_API_KEY`
3. Install dependencies: pip install anthropic python-dotenv pymupdf
4. Run: python resumeReviewer/resume_reviewer.py
5. Enter the path to your resume PDF when prompted
6. Choose general or targeted review mode
