import os
from dotenv import load_dotenv
import anthropic
from query import get_connection, search_by_keywords, get_all_experience, format_for_prompt

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def extract_keywords(job_description):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system="""Extract technical skills, tools, and qualifications from a job description. 
Return only a comma-separated list of single keywords or short phrases. 
Focus on: programming languages, frameworks, platforms, tools, and technical concepts.
Example output: Python, AWS, REST APIs, machine learning, SQL, React
Return nothing else — no explanation, no numbering, just the comma-separated list.""",
        messages=[{"role": "user", "content": job_description}]
    )
    raw = message.content[0].text.strip()
    keywords = [k.strip().lower() for k in raw.split(",")]
    
    input_cost = (message.usage.input_tokens / 1_000_000) * 3.00
    output_cost = (message.usage.output_tokens / 1_000_000) * 15.00
    return keywords, input_cost + output_cost

def generate_resume_content(job_description, projects, skills, experience):
    background = format_for_prompt(projects, skills, experience)
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system="""You are a professional resume writer. Given a candidate's background and a job description, generate a tailored resume in this EXACT format:

SUMMARY
[2-3 sentence professional summary tailored to the job]

SKILLS
[comma-separated list of the most relevant skills from the candidate's background]

PROJECT: [project name] | [date]
TECHNOLOGIES: [technologies used]
BULLETS:
- [achievement-focused bullet point]
- [achievement-focused bullet point]

PROJECT: [next project name] | [date]
TECHNOLOGIES: [technologies used]
BULLETS:
- [bullet point]
- [bullet point]

EXPERIENCE: [role] | [organization] | [start] - [end]
BULLETS:
- [bullet point]
- [bullet point]

Rules:
- Only include projects and experience from the candidate's background
- Select the 3 most relevant projects maximum
- Write bullets that emphasize impact and relevance to the job
- Keep each bullet point to ONE line maximum — concise and punchy, not verbose
- Maximum 2 bullets per project, 2 bullets for experience
- Never invent technologies or experience not in the background
- Follow the format exactly — the output will be parsed by code""",
        messages=[{"role": "user", "content": f"CANDIDATE BACKGROUND:\n{background}\n\nJOB DESCRIPTION:\n{job_description}"}]
    )
    
    input_cost = (message.usage.input_tokens / 1_000_000) * 3.00
    output_cost = (message.usage.output_tokens / 1_000_000) * 15.00
    return message.content[0].text.strip(), input_cost + output_cost

if __name__ == "__main__":
    print("=== Resume Generator ===\n")
    
    print("Paste your job description below. Type 'DONE' on a new line when finished:\n")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "DONE":
            break
        lines.append(line)
    job_description = "\n".join(lines)
    
    if not job_description.strip():
        print("No job description provided. Exiting.")
        exit()
    
    print("\nStep 1: Extracting keywords from job description...")
    keywords, cost1 = extract_keywords(job_description)
    print(f"Keywords found: {', '.join(keywords)}")
    
    print("\nStep 2: Searching database for relevant experience...")
    projects, skills, _ = search_by_keywords(keywords)
    experience = get_all_experience()
    print(f"Found {len(projects)} relevant projects, {len(skills)} skills")
    
    if not projects and not skills:
        print("No matching entries found. Consider adding more projects to your database.")
        exit()
    
    print("\nStep 3: Generating tailored resume content...")
    resume_content, cost2 = generate_resume_content(job_description, projects, skills, experience)
    
    total_cost = cost1 + cost2
    print(f"\n--- Usage ---")
    print(f"Total cost: ${total_cost:.6f}")
    
    print("\n--- Generated Resume Content ---\n")
    print(resume_content)
    
    save = input("\nSave as PDF? (y/n): ").strip().lower()
    if save == "y":
        from resume_generator import generate_pdf
        name = input("Enter your full name: ").strip()
        contact = input("Enter contact info (email | phone | linkedin): ").strip()
        filename = input("Output filename (e.g. resume.pdf): ").strip()
        generate_pdf(resume_content, name, contact, filename)
        print(f"Resume saved as {filename}")