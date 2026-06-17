import os
import fitz  # pymupdf
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if not text.strip():
            print("Warning: No text could be extracted from this PDF.")
            print("The PDF may be scanned or image-based. Try a text-based PDF.")
            exit()
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        exit()

def build_system_prompt(mode, job_info=None):
    base = """You are an experienced technical recruiter and hiring manager with 10+ years 
reviewing resumes for software engineering roles. 

Your job is to give honest, direct, actionable feedback. Do not sugarcoat.

Structure your response EXACTLY like this:

ISSUES TO FIX
- [Describe the specific problem and exactly how to fix it]
- [Each issue on its own line]

QUICK WINS
- [Small, high-impact changes that take under 10 minutes]
- [Be specific — don't say 'improve formatting', say what exactly to change]

GENERAL IMPRESSION
[2-3 sentences max. Be direct. Would this resume get past an initial screen?]
"""
    
    if mode == "targeted" and job_info:
        base += f"""
JOB FIT GAPS
Based on the target role: {job_info}
- [List specific skills, keywords, or experience missing for this role]
- [Flag any mismatches between the resume and what this role typically requires]
"""
    return base

def review_resume(resume_text, mode, job_info=None):
    system_prompt = build_system_prompt(mode, job_info)
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Please review this resume:\n\n{resume_text}"}
            ]
        )
    except anthropic.BadRequestError as e:
        print(f"API rejected the request: {e}")
        exit()
    except anthropic.APIConnectionError:
        print("Could not connect to the API. Check your internet connection.")
        exit()
    except anthropic.AuthenticationError:
        print("Invalid API key. Check your .env file.")
        exit()
    except Exception as e:
        print(f"Unexpected error calling API: {e}")
        exit()
    
    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    input_cost = (input_tokens / 1_000_000) * 3.00
    output_cost = (output_tokens / 1_000_000) * 15.00
    total_cost = input_cost + output_cost
    
    print(f"\n--- Usage ---")
    print(f"Input tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Cost:          ${total_cost:.6f}\n")
    
    return message.content[0].text

if __name__ == "__main__":
    print("=== Resume Reviewer ===\n")
    
    pdf_path = input("Enter the path to your resume PDF: ").strip()
    
    if not os.path.exists(pdf_path):
        print("File not found. Please check the path and try again.")
        exit()
    
    print("\nReview mode:")
    print("1. General (no target job)")
    print("2. Targeted (specific job role)")
    mode_choice = input("\nEnter 1 or 2: ").strip()
    
    job_info = None
    if mode_choice == "2":
        job_info = input("Enter the job title or paste the job description: ").strip()
        mode = "targeted"
    else:
        mode = "general"
    
    print("\nExtracting resume text...")
    resume_text = extract_text_from_pdf(pdf_path)
    
    print("Analyzing resume...\n")
    result = review_resume(resume_text, mode, job_info)
    print(result)