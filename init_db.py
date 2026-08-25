import sqlite3

def init_db():
    conn = sqlite3.connect('interview_bot.db')
    cursor = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
        
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    
    print("SQLite database (interview_bot.db) initialized successfully.")

if __name__ == "__main__":
    init_db()
