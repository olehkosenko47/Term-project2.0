import sqlite3

def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE)")
    cursor.execute("CREATE TABLE IF NOT EXISTS contacts (user TEXT, contact TEXT)")
    conn.commit()
    conn.close()

def create_user(username):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_contacts(username):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contact FROM contacts WHERE user = ?", (username,))
    contacts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return contacts

def add_contact(user, contact):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO contacts (user, contact) VALUES (?, ?)", (user, contact))
    conn.commit()
    conn.close()