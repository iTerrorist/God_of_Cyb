import sqlite3, time
import os

DB_PATH = os.getenv("DB_PATH", "users.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    expire INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender INTEGER,
    target TEXT,
    type TEXT,
    reason TEXT,
    image TEXT,
    time INTEGER
)
""")
conn.commit()

def add_user(user_id, days):
    expire = int(time.time()) + days * 86400
    cur.execute("INSERT OR REPLACE INTO users VALUES (?,?)", (user_id, expire))
    conn.commit()

def is_allowed(user_id):
    cur.execute("SELECT expire FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row and row[0] > int(time.time())

def save_report(sender, target, type_, reason, image=None):
    cur.execute(
        "INSERT INTO reports VALUES (NULL,?,?,?,?,?,?)",
        (sender, target, type_, reason, image, int(time.time()))
    )
    conn.commit()
