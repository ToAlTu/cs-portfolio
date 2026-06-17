# Experience DB — AI Resume Generator

A command-line tool that stores your professional background in a PostgreSQL database and generates a tailored, one-page resume PDF using the Claude API.

## How it works
1. Your projects, skills, and work experience live in a local PostgreSQL database
2. Paste a job description — Claude extracts relevant keywords
3. PostgreSQL full-text search finds your most relevant experience
4. Claude generates tailored resume content from the filtered results
5. Output is saved as a clean one-page PDF

## Setup

1. Install PostgreSQL from https://www.postgresql.org/download/windows/

2. Open SQL Shell (psql) and run:

```sql
CREATE USER devuser WITH PASSWORD 'your-password';
CREATE DATABASE experience OWNER devuser;
GRANT ALL PRIVILEGES ON DATABASE experience TO devuser;
```

3. Create a virtual environment and install dependencies:

```
pip install anthropic python-dotenv psycopg2-binary reportlab
```

4. Create a `.env` file in the project folder:

```
ANTHROPIC_API_KEY=your-key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=experience
DB_USER=devuser
DB_PASSWORD=your-password
```

5. Run setup to create the database tables:

```
python setup_db.py
```

6. Add your experience using the management tool:

```
python manage.py
```

7. Generate a tailored resume:

```
python main.py
```

## Files

- `setup_db.py` — creates the database tables
- `manage.py` — CLI tool to add, view, and remove entries (AI-assisted descriptions)
- `query.py` — database queries and full-text search
- `main.py` — orchestrates keyword extraction, search, and resume generation
- `resume_generator.py` — converts Claude's output into a PDF
