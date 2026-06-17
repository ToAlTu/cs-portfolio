import os
from dotenv import load_dotenv
import psycopg2
import anthropic
from query import get_connection

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_description(name, technologies, user_description):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system="""You write concise, keyword-rich project descriptions for technical resumes and databases. 
Your descriptions are 2-3 sentences, use industry-standard terminology, and naturally include relevant technical concepts without being generic. 
Never use phrases like 'leveraged' or 'utilized'. Be specific and concrete.
Return only the description text, nothing else.""",
        messages=[{"role": "user", "content": f"Project name: {name}\nTechnologies: {technologies}\nWhat the person said about it: {user_description}\n\nWrite a rich project description."}]
    )
    return message.content[0].text.strip()

def add_project(conn):
    print("\n--- Add Project ---")
    name = input("Project name: ").strip()
    date = input("Date (e.g. May 2025): ").strip()
    
    print("What technologies did you use? (comma separated): ")
    tech_input = input().strip()
    technologies = [t.strip() for t in tech_input.split(",")]
    
    print("Briefly describe what you built and what it does: ")
    user_description = input().strip()
    
    print("\nGenerating description...")
    description = generate_description(name, ", ".join(technologies), user_description)
    
    print(f"\nGenerated description:\n{description}")
    confirm = input("\nUse this description? (y/n): ").strip().lower()
    
    if confirm == "n":
        print("Enter your own description: ")
        description = input().strip()
    
    print("What was the outcome or result of this project? ")
    outcome = input().strip()
    
    with conn.cursor() as cur:
        cur.execute("INSERT INTO projects (name, description, outcome, date) VALUES (%s, %s, %s, %s) RETURNING id", (name, description, outcome, date))
        project_id = cur.fetchone()[0]
        
        for tech_name in technologies:
            cur.execute("SELECT id FROM technologies WHERE LOWER(name) = LOWER(%s)", (tech_name,))
            result = cur.fetchone()
            
            if result:
                tech_id = result[0]
            else:
                print(f"'{tech_name}' not found in technologies — adding it.")
                category = input(f"Category for '{tech_name}' (language/backend/cloud/frontend/tool/api): ").strip()
                cur.execute("INSERT INTO technologies (name, category) VALUES (%s, %s) RETURNING id", (tech_name, category))
                tech_id = cur.fetchone()[0]
            
            cur.execute("INSERT INTO project_technologies (project_id, technology_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (project_id, tech_id))
        
        conn.commit()
    print(f"\nProject '{name}' added successfully.")

def add_skill(conn):
    print("\n--- Add Skill ---")
    name = input("Skill name: ").strip()
    category = input("Category (language/backend/cloud/frontend/tool/api): ").strip()
    proficiency = input("Proficiency (proficient/familiar): ").strip()
    
    with conn.cursor() as cur:
        cur.execute("INSERT INTO skills (name, category, proficiency) VALUES (%s, %s, %s) ON CONFLICT (name) DO UPDATE SET category=%s, proficiency=%s", (name, category, proficiency, category, proficiency))
        conn.commit()
    print(f"Skill '{name}' added successfully.")

def add_experience(conn):
    print("\n--- Add Work Experience ---")
    role = input("Job title/role: ").strip()
    organization = input("Company/organization: ").strip()
    start_date = input("Start date (e.g. June 2023): ").strip()
    end_date = input("End date (or 'Present'): ").strip()
    
    print("What did you do in this role? (brief summary): ")
    user_description = input().strip()
    
    print("What technologies did you use? (comma separated, or press Enter to skip): ")
    tech_input = input().strip()
    technologies = [t.strip() for t in tech_input.split(",")] if tech_input else []
    
    print("\nGenerating responsibilities description...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system="""You write concise, keyword-rich work experience descriptions for technical resumes. 
2-3 sentences, use industry-standard terminology, focus on impact and technical scope.
Never use 'leveraged' or 'utilized'. Return only the description text.""",
        messages=[{"role": "user", "content": f"Role: {role} at {organization}\nTechnologies: {', '.join(technologies)}\nWhat they did: {user_description}\n\nWrite a responsibilities description."}]
    )
    responsibilities = message.content[0].text.strip()
    
    print(f"\nGenerated responsibilities:\n{responsibilities}")
    confirm = input("\nUse this? (y/n): ").strip().lower()
    if confirm == "n":
        print("Enter your own: ")
        responsibilities = input().strip()
    
    with conn.cursor() as cur:
        cur.execute("INSERT INTO experience (role, organization, start_date, end_date, responsibilities) VALUES (%s, %s, %s, %s, %s) RETURNING id", (role, organization, start_date, end_date, responsibilities))
        exp_id = cur.fetchone()[0]
        
        for tech_name in technologies:
            cur.execute("SELECT id FROM technologies WHERE LOWER(name) = LOWER(%s)", (tech_name,))
            result = cur.fetchone()
            if result:
                tech_id = result[0]
            else:
                category = input(f"Category for '{tech_name}': ").strip()
                cur.execute("INSERT INTO technologies (name, category) VALUES (%s, %s) RETURNING id", (tech_name, category))
                tech_id = cur.fetchone()[0]
            cur.execute("INSERT INTO experience_technologies (experience_id, technology_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (exp_id, tech_id))
        
        conn.commit()
    print(f"\nExperience '{role}' added successfully.")

def view_all(conn):
    with conn.cursor() as cur:
        print("\n--- Projects ---")
        cur.execute("SELECT name, date FROM projects ORDER BY date DESC")
        for row in cur.fetchall():
            print(f"  {row[0]} ({row[1]})")
        
        print("\n--- Skills ---")
        cur.execute("SELECT name, category, proficiency FROM skills ORDER BY category")
        for row in cur.fetchall():
            print(f"  {row[0]} ({row[1]}) - {row[2]}")
        
        print("\n--- Experience ---")
        cur.execute("SELECT role, organization, start_date, end_date FROM experience")
        for row in cur.fetchall():
            print(f"  {row[0]} at {row[1]} ({row[2]} - {row[3]})")

def remove_entry(conn):
    print("\nWhat would you like to remove?")
    print("1. Project")
    print("2. Skill")
    print("3. Experience")
    choice = input("Enter 1, 2, or 3: ").strip()
    
    with conn.cursor() as cur:
        if choice == "1":
            cur.execute("SELECT id, name FROM projects")
            projects = cur.fetchall()
            for p in projects:
                print(f"  {p[0]}. {p[1]}")
            pid = input("Enter project ID to remove: ").strip()
            cur.execute("DELETE FROM projects WHERE id = %s", (pid,))
            print("Project removed.")
        elif choice == "2":
            name = input("Skill name to remove: ").strip()
            cur.execute("DELETE FROM skills WHERE LOWER(name) = LOWER(%s)", (name,))
            print("Skill removed.")
        elif choice == "3":
            cur.execute("SELECT id, role, organization FROM experience")
            for e in cur.fetchall():
                print(f"  {e[0]}. {e[1]} at {e[2]}")
            eid = input("Enter experience ID to remove: ").strip()
            cur.execute("DELETE FROM experience WHERE id = %s", (eid,))
            print("Experience removed.")
        conn.commit()

if __name__ == "__main__":
    print("=== Experience DB Manager ===")
    conn = get_connection()
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Add project")
        print("2. Add skill")
        print("3. Add work experience")
        print("4. View all entries")
        print("5. Remove an entry")
        print("6. Exit")
        
        choice = input("\nEnter 1-6: ").strip()
        
        if choice == "1":
            add_project(conn)
        elif choice == "2":
            add_skill(conn)
        elif choice == "3":
            add_experience(conn)
        elif choice == "4":
            view_all(conn)
        elif choice == "5":
            remove_entry(conn)
        elif choice == "6":
            print("Goodbye.")
            conn.close()
            break
        else:
            print("Invalid choice, try again.")