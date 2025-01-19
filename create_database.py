import sqlite3
import pandas as pd

# Path to the CSV file
csv_file = "data/Crop_recommendation.csv"

# Path to the SQLite database
db_file = "data/crop_recommendation.db"

# Connect to SQLite and create table
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create crops table
cursor.execute('''
CREATE TABLE IF NOT EXISTS crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    N REAL,
    P REAL,
    K REAL,
    temperature REAL,
    humidity REAL,
    ph REAL,
    rainfall REAL,
    crop TEXT
)
''')

# Load the CSV data and insert it into the table
df = pd.read_csv(csv_file)
df.to_sql("crops", conn, if_exists="replace", index=False)

print("Database and table created successfully!")

conn.close()
