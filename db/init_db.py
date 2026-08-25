import sqlite3
import os

def init_db():
    # Get the directory where this script is located (the 'db' folder)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the data directory (one level up, then into 'data')
    data_dir = os.path.join(current_dir, '..', 'data')
    
    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Paths for DB and schema
    db_path = os.path.join(data_dir, 'interview_bot.db')
    schema_path = os.path.join(current_dir, 'schema.sql')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
        
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    
    print(f"SQLite database initialized successfully at: {db_path}")

if __name__ == "__main__":
    init_db()
