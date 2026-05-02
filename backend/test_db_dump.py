import sqlite3
import pandas as pd

db_path = r"c:\Users\Tanya\OneDrive\Desktop\FinYaarProj\instance\finyaar.db"
out_path = r"c:\Users\Tanya\OneDrive\Desktop\FinYaarProj\db_dump_utf8.txt"

with open(out_path, "w", encoding="utf-8") as f:
    conn = sqlite3.connect(db_path)
    
    f.write("=== ALL TABLES IN DATABASE ===\n")
    tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
    tables = pd.read_sql_query(tables_query, conn)
    f.write(tables.to_string(index=False) + "\n")
    f.write("\n" + "="*50 + "\n")
    
    if 'users' in tables['name'].values:
        f.write("=== USERS TABLE DATA ===\n")
        users_query = "SELECT * FROM users;"
        users_df = pd.read_sql_query(users_query, conn)
        f.write(users_df.to_string(index=False) + "\n")
    else:
        f.write("Users table not found!\n")
        
    conn.close()
