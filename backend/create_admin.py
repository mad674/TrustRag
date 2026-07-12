"""Create an admin user for local development.
Run: python create_admin.py username email password
"""
import sys
from app.db import SessionLocal
from app.crud import get_user_by_username, create_user


def main():
    if len(sys.argv) < 4:
        print("Usage: python create_admin.py username email password")
        return
    username, email, password = sys.argv[1:4]
    db = SessionLocal()
    existing = get_user_by_username(db, username)
    if existing:
        print("User exists")
        return
    class U:
        def __init__(self, username, email, password):
            self.username = username
            self.email = email
            self.password = password

    create_user(db, U(username, email, password), role='admin')
    print('Admin user created')


if __name__ == '__main__':
    main()
