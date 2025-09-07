import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('instance/vendor_timesheet.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("🗄️ DATABASE STRUCTURE:")
        print(f"Database: vendor_timesheet.db")
        print(f"Total Tables: {len(tables)}")
        print()
        
        for table in tables:
            table_name = table[0]
            print(f"📋 Table: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name, col_type = col[1], col[2]
                print(f"  - {col_name}: {col_type}")
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Records: {count}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    check_database()
