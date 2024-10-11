"""Run once to create the db tables."""
from youbet.app import app, db


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
