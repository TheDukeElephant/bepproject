from app.database import init_db, add_user

if __name__ == "__main__":
    init_db()
    add_user('pi', 'BEP04')  # Default user
    print("Database initialized with default user.")
