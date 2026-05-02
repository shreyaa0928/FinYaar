import sqlite3
import pandas as pd
import os

db_path = r"instance\finyaar.db"

if not os.path.exists(db_path):
    print("Database file not found at", db_path)
    exit()

conn = sqlite3.connect(db_path)

print("\n" + "="*50)
print("              DATABASE TABLES")
print("="*50)
tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
tables = pd.read_sql_query(tables_query, conn)
print(tables.to_string(index=False))
print("="*50 + "\n")

while True:
    table_name = input("\nEnter table name to view (or press Enter/Return to exit): ").strip()
    
    if not table_name:
        print("Exiting...")
        break
        
    if table_name in tables['name'].values:
        print(f"\n--- DATA FOR TABLE: {table_name.upper()} ---")
        
        # We can hide password for users table specifically if you show it to others
        if table_name == 'users':
            query = "SELECT user_id, name, email, student_id, course, year, budget, paper_cash, role FROM users;"
        else:
            query = f"SELECT * FROM {table_name};"
            
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            print("Table is empty (No data yet).")
        else:
            print(df.to_string(index=False))
    else:
        print(f"Table '{table_name}' does not exist. Please check spelling.")

conn.close()
