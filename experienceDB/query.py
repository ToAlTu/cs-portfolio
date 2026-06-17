import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def get_all_projects():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT p.id, p.name, p.description, p.outcome, p.date FROM projects p ORDER BY p.date DESC")
        projects = cur.fetchall()
        result = []
        for project in projects:
            project_id, name, description, outcome, date = project
            cur.execute("SELECT t.name FROM technologies t JOIN project_technologies pt ON t.id = pt.technology_id WHERE pt.project_id = %s", (project_id,))
            techs = [row[0] for row in cur.fetchall()]
            result.append({"name": name, "description": description, "outcome": outcome, "date": date, "technologies": techs})
    conn.close()
    return result

def get_all_skills():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name, category, proficiency FROM skills ORDER BY category, name")
        rows = cur.fetchall()
    conn.close()
    return [{"name": r[0], "category": r[1], "proficiency": r[2]} for r in rows]

def get_all_experience():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, role, organization, start_date, end_date, responsibilities FROM experience")
        rows = cur.fetchall()
        result = []
        for row in rows:
            exp_id, role, org, start, end, resp = row
            cur.execute("SELECT t.name FROM technologies t JOIN experience_technologies et ON t.id = et.technology_id WHERE et.experience_id = %s", (exp_id,))
            techs = [r[0] for r in cur.fetchall()]
            result.append({"role": role, "organization": org, "start_date": start, "end_date": end, "responsibilities": resp, "technologies": techs})
    conn.close()
    return result

def format_for_prompt(projects, skills, experience):
    output = "=== PROJECTS ===\n"
    for p in projects:
        output += f"\n{p['name']} ({p['date']})\n"
        output += f"Description: {p['description']}\n"
        output += f"Outcome: {p['outcome']}\n"
        output += f"Technologies: {', '.join(p['technologies'])}\n"

    output += "\n=== SKILLS ===\n"
    for s in skills:
        output += f"{s['name']} ({s['category']}) - {s['proficiency']}\n"

    output += "\n=== WORK EXPERIENCE ===\n"
    for e in experience:
        output += f"\n{e['role']} at {e['organization']}\n"
        output += f"{e['start_date']} - {e['end_date']}\n"
        output += f"{e['responsibilities']}\n"
        output += f"Technologies: {', '.join(e['technologies'])}\n"

    return output

def search_by_keywords(keywords):
    conn = get_connection()
    
    # Clean keywords — tsquery only accepts single words, no special characters
    clean_keywords = []
    for kw in keywords:
        # Take only the first word of multi-word phrases, remove special characters
        word = kw.split()[0] if kw.split() else ""
        word = ''.join(c for c in word if c.isalpha())
        if len(word) > 2:  # skip very short words
            clean_keywords.append(word)
    
    # Remove duplicates
    clean_keywords = list(set(clean_keywords))
    ts_query = " | ".join(clean_keywords)
    
    print(f"Database search terms: {ts_query}")
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT p.id, p.name, p.description, p.outcome, p.date
            FROM projects p
            WHERE to_tsvector('english', p.name || ' ' || p.description || ' ' || p.outcome)
            @@ to_tsquery('english', %s)
        """, (ts_query,))
        projects = cur.fetchall()
        
        matched_projects = []
        for project in projects:
            project_id, name, description, outcome, date = project
            cur.execute("SELECT t.name FROM technologies t JOIN project_technologies pt ON t.id = pt.technology_id WHERE pt.project_id = %s", (project_id,))
            techs = [row[0] for row in cur.fetchall()]
            matched_projects.append({"name": name, "description": description, "outcome": outcome, "date": date, "technologies": techs})

        cur.execute("""
            SELECT e.id, e.role, e.organization, e.start_date, e.end_date, e.responsibilities
            FROM experience e
            WHERE to_tsvector('english', e.role || ' ' || e.responsibilities)
            @@ to_tsquery('english', %s)
        """, (ts_query,))
        experience = cur.fetchall()
        
        matched_experience = []
        for row in experience:
            exp_id, role, org, start, end, resp = row
            cur.execute("SELECT t.name FROM technologies t JOIN experience_technologies et ON t.id = et.technology_id WHERE et.experience_id = %s", (exp_id,))
            techs = [r[0] for r in cur.fetchall()]
            matched_experience.append({"role": role, "organization": org, "start_date": start, "end_date": end, "responsibilities": resp, "technologies": techs})

        cur.execute("""
            SELECT name, category, proficiency FROM skills
            WHERE to_tsvector('english', name || ' ' || category)
            @@ to_tsquery('english', %s)
        """, (ts_query,))
        matched_skills = [{"name": r[0], "category": r[1], "proficiency": r[2]} for r in cur.fetchall()]

    conn.close()
    return matched_projects, matched_skills, matched_experience

def test_search():
    keywords = ["python", "AI", "API", "javascript", "AWS", "react", "SQL"]
    projects, skills, experience = search_by_keywords(keywords)
    
    print(f"Matched {len(projects)} projects:")
    for p in projects:
        print(f"  - {p['name']}")
    
    print(f"\nMatched {len(skills)} skills:")
    for s in skills:
        print(f"  - {s['name']}")
    
    print(f"\nMatched {len(experience)} experience entries:")
    for e in experience:
        print(f"  - {e['role']}")

if __name__ == "__main__":
    print("=== Testing keyword search ===\n")
    test_search()