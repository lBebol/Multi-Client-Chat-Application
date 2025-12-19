# storage.py
import sqlite3
import os

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "chat.db")


# =========================
# Database initialization
# =========================

def init_db():
    """
    Creates the database file and messages table if they do not exist.
    """
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts INTEGER NOT NULL,
            sender TEXT NOT NULL,
            scope TEXT NOT NULL,   -- 'group' or 'pm'
            target TEXT,
            text TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# Message persistence
# =========================

def save_message(ts, sender, scope, target, text):
    """
    Stores a message in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages (ts, sender, scope, target, text)
        VALUES (?, ?, ?, ?, ?)
    """, (ts, sender, scope, target, text))

    conn.commit()
    conn.close()


# =========================
# History retrieval
# =========================

def load_group_history(limit=50):
    """
    Returns the most recent group messages as a list of dicts.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT ts, sender, text
        FROM messages
        WHERE scope = 'group'
        ORDER BY ts ASC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "ts": ts,
            "sender": sender,
            "scope": "group",
            "target": None,
            "text": text
        }
        for ts, sender, text in rows
    ]


def load_private_history(user1, user2, limit=50):
    """
    Returns private message history between two users as a list of dicts.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT ts, sender, target, text
        FROM messages
        WHERE scope = 'pm'
          AND (
                (sender = ? AND target = ?)
             OR (sender = ? AND target = ?)
          )
        ORDER BY ts ASC
        LIMIT ?
    """, (user1, user2, user2, user1, limit))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "ts": ts,
            "sender": sender,
            "scope": "pm",
            "target": target,
            "text": text
        }
        for ts, sender, target, text in rows
    ]

def load_pm_partners(username):
    """
    Returns a list of usernames that have private message history with `username`.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT
            CASE
                WHEN sender = ? THEN target
                ELSE sender
            END
        FROM messages
        WHERE scope = 'pm'
          AND (sender = ? OR target = ?)
    """, (username, username, username))

    rows = cur.fetchall()
    conn.close()

    return [row[0] for row in rows if row[0]]
