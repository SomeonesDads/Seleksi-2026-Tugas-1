import os
import sys
import subprocess
import psycopg2

# Add Data Storing/src to path to import load_data
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data Storing', 'src'))
from load_data import load

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "hsr_db",
    "user":     "postgres",
    "password": "Undertale",
}

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Run Data Scraping/src/main.py
    print("--- 1. Run Data Scraping ---")
    scraping_src = os.path.join(root_dir, 'Data Scraping', 'src')
    scraping_main = os.path.join(scraping_src, 'main.py')
    
    try:
        subprocess.run([sys.executable, scraping_main], cwd=scraping_src, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Data Scraping failed with error: {e}")
        return

        
    # 2. Run schema.sql
    print("\n--- 2. Push schema.sql ---")
    schema_path = os.path.join(root_dir, 'Data Storing', 'src', 'schema.sql')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        
    print(f"Connecting to database {DB_CONFIG['dbname']} at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.close()
        print("Schema executed successfully.")
    except psycopg2.Error as e:
        print(f"Notice during schema execution: {e}")
        print("This might be expected if the tables already exist.")
        
    # 3. Run load() in load_data.py
    print("\n--- 3. Run load_data.load() ---")
    try:
        load(DB_CONFIG)
    except Exception as e:
        print(f"Data loading failed: {e}")

main()