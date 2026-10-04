import json
import hashlib
import os

USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def sign_up(name, phone, password):
    users = load_users()

    if phone in users:
        return False, "An account with this number already exists."

    users[phone] = {
        "name": name,
        "phone": phone,
        "password": hash_password(password)
    }

    save_users(users)
    return True, "Account created successfully!"


def sign_in(phone, password):
    users = load_users()

    if phone not in users:
        return False, "No account found with this number."

    if users[phone]["password"] != hash_password(password):
        return False, "Incorrect password."

    return True, users[phone]["name"]