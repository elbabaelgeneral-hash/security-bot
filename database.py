import sqlite3

DB_PATH = "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, points INTEGER DEFAULT 0,
        language TEXT DEFAULT 'ar', referred_by INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS force_subs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, chat_id TEXT,
        title TEXT, invite_link TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT,
        details TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, target TEXT,
        reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, referred_by=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone():
        conn.close()
        return False
    c.execute("INSERT INTO users (user_id, username, first_name, referred_by) VALUES (?, ?, ?, ?)",
              (user_id, username, first_name, referred_by))
    conn.commit()
    conn.close()
    return True

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, points, language, referred_by FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def add_points(user_id, pts):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (pts, user_id))
    conn.commit()
    conn.close()

def get_points(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def get_users_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    n = c.fetchone()[0]
    conn.close()
    return n

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT first_name, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_history(user_id, action, details=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, action, details) VALUES (?, ?, ?)", (user_id, action, details))
    conn.commit()
    conn.close()

def get_history(user_id, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT action, details, created_at FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def add_report(user_id, target, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO reports (user_id, target, reason) VALUES (?, ?, ?)", (user_id, target, reason))
    conn.commit()
    conn.close()

def get_reports():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, user_id, target, reason, created_at FROM reports ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return rows

def add_force_sub(sub_type, chat_id, title, invite_link=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO force_subs (type, chat_id, title, invite_link) VALUES (?, ?, ?, ?)",
              (sub_type, chat_id, title, invite_link))
    conn.commit()
    conn.close()

def get_force_subs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, type, chat_id, title, invite_link FROM force_subs")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_force_sub(sub_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM force_subs WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()


def deduct_points(user_id, pts):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET points = MAX(0, points - ?) WHERE user_id = ?", (pts, user_id))
    conn.commit()
    conn.close()

def find_user(query):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        uid = int(query)
        c.execute("SELECT user_id, first_name, points FROM users WHERE user_id = ?", (uid,))
        row = c.fetchone()
        if row:
            conn.close()
            return row
    except:
        pass
    q = query.lstrip('@')
    c.execute("SELECT user_id, first_name, points FROM users WHERE username = ?", (q,))
    row = c.fetchone()
    conn.close()
    return row


def get_setting(key, default="1"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
