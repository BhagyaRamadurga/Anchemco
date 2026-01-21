import sqlite3

# Connect to database
conn = sqlite3.connect('sharanu_app.db')
cursor = conn.cursor()

try:
    # Add column
    cursor.execute("ALTER TABLE production_entry ADD COLUMN batch_quantity TEXT")
    print("Column added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error (maybe column exists): {e}")

conn.commit()
conn.close()
