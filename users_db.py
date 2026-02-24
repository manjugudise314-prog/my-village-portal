import sqlite3
import bcrypt

# create table automatically
def create_users_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    conn.commit()
    conn.close()

create_users_table()


# password encryption
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)


# register user
def register_user(name, phone, email, password, role="user"):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    hashed = hash_password(password)

    c.execute(
        "INSERT INTO users (name, phone, email, password, role) VALUES (?,?,?,?,?)",
        (name, phone, email, hashed, role)
    )

    conn.commit()
    conn.close()


# login check
def login_user(email, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT password, role FROM users WHERE email=?", (email,))
    result = c.fetchone()

    conn.close()

    if result:
        stored_password, role = result
        if verify_password(password, stored_password):
            return True, role

    return False, None