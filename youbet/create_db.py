"""Run once to create the db tables."""
import sys
from youbet.app import app, db
from youbet import lib
from youbet.database import User, Event, Round


TEST_DATA = {
    "users": [
        {"name": "a", "email": "a@a.com", "password": "a"},
        {"name": "b", "email": "b@b.com", "password": "b"},
        {"name": "c", "email": "c@c.com", "password": "c"},
    ],
    "events": [
        {"name": "Event 1", "starting_money": 100, "creator": "a"},
        {"name": "Event 2", "starting_money": 500, "creator": "b"},
    ]
}


if __name__ == "__main__":
    with app.app_context():
        if "--clear" in sys.argv:
            print("Wiping existing database tables...")
            db.drop_all()
        print("Building database tables...")
        db.create_all()
    
        if "--test" in sys.argv:
            print("Adding test data rows...")
            users = {}
            for user_data in TEST_DATA["users"]:
                encrypted_password, salt = lib.hash_password(user_data["password"], as_str=True)
                user = User(name=user_data["name"], email=user_data["email"], password=encrypted_password, salt=salt)
                users[user_data["name"]] = user
                db.session.add(user)
            
            for event_data in TEST_DATA["events"]:
                event = Event(name=event_data["name"], starting_money=event_data["starting_money"], creator=users[event_data["creator"]])
                db.session.add(event)
            db.session.commit()
            