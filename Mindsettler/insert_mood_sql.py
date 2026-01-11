"""Insert mood data using raw SQL"""
import sqlite3
from datetime import date, timedelta

# Connect to database
conn = sqlite3.connect('D:/projects/GWOC-1/Mindsettler/db.sqlite3')
cursor = conn.cursor()

# Get user ID for 'hpv'
cursor.execute("SELECT id FROM auth_user WHERE username = 'hpv'")
user_id = cursor.fetchone()[0]
print(f"User ID for 'hpv': {user_id}")

# Clear existing mood entries
cursor.execute("DELETE FROM users_moodentry WHERE user_id = ?", (user_id,))
print(f"Cleared existing mood entries")

# Create mood entries
today = date.today()
mood_scores = [7, 6, 8, 5, 7, 9, 6, 8, 7, 5, 8, 6, 7, 8, 9, 7, 6, 8, 7, 8, 6, 7, 9, 8, 7, 6, 8, 7, 8, 6]

for i, score in enumerate(mood_scores):
    entry_date = today - timedelta(days=29-i)
    cursor.execute(
        "INSERT INTO users_moodentry (user_id, mood_score, date, note, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (user_id, score, entry_date.isoformat(), f"Mood entry for {entry_date}")
    )
    print(f"Inserted {entry_date}: {score}/10")

conn.commit()
print(f"\nSuccessfully created {len(mood_scores)} mood entries!")

# Verify
cursor.execute("SELECT COUNT(*) FROM users_moodentry WHERE user_id = ?", (user_id,))
count = cursor.fetchone()[0]
print(f"Total mood entries in database: {count}")

conn.close()
