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

def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS technologies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(50)
            );
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                outcome TEXT,
                date VARCHAR(20)
            );
            CREATE TABLE IF NOT EXISTS project_technologies (
                project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
                technology_id INTEGER REFERENCES technologies(id) ON DELETE CASCADE,
                PRIMARY KEY (project_id, technology_id)
            );
            CREATE TABLE IF NOT EXISTS experience (
                id SERIAL PRIMARY KEY,
                role VARCHAR(200) NOT NULL,
                organization VARCHAR(200),
                start_date VARCHAR(20),
                end_date VARCHAR(20),
                responsibilities TEXT
            );
            CREATE TABLE IF NOT EXISTS experience_technologies (
                experience_id INTEGER REFERENCES experience(id) ON DELETE CASCADE,
                technology_id INTEGER REFERENCES technologies(id) ON DELETE CASCADE,
                PRIMARY KEY (experience_id, technology_id)
            );
            CREATE TABLE IF NOT EXISTS skills (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(50),
                proficiency VARCHAR(50)
            );
        """)
        conn.commit()
        print("Tables created successfully.")

if __name__ == "__main__":
    print("Setting up database...")
    conn = get_connection()
    create_tables(conn)
    conn.close()
    print("Done. Use manage.py to add your experience.")