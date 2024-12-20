
from youbet.database import User, Event, Round, Wager
from youbet import lib

def test_db_create(db):
    print(db)


def test_user(db):
    user = User(name="test", email="test", password="test", salt=lib.generate_salt())
    db.session.add(user)
    db.session.commit()

    round_trip = db.session.get(User, user.id)
    round_trip == user


def test_event(db):
    user = User(name="test", email="test", password="test", salt=lib.generate_salt())
    event = Event(name="test", starting_money=100, active=True, joinable=True, creator=user)
    db.session.add(event)
    db.session.commit()

    round_trip = db.session.get(Event, event.id)
    round_trip == event

    assert event.creator == user


def test_round(db):
    user = User(name="test", email="test", password="test", salt=lib.generate_salt())
    event = Event(name="test", starting_money=100, active=True, joinable=True, creator=user)
    round = Round(name="test", event=event)
    db.session.add(round)
    db.session.commit()

    round_trip = db.session.get(Round, round.id)
    round_trip == round

    assert round.event == event
    assert round in event.rounds


def test_wager(db):
    user = User(name="test", email="test", password="test", salt=lib.generate_salt())
    event = Event(name="test", starting_money=100, active=True, joinable=True, creator=user)
    round = Round(name="test", event=event)
    wager = Wager(amount=1.0, user=user, stake=user, round=round)
    db.session.add(wager)
    db.session.commit()

    round_trip = db.session.get(Wager, wager.id)
    round_trip == wager

    assert wager.user == user
    assert wager.stake == user
    assert wager.round == round


def test_wager_get_outcome(db):
    user_a = User(name="test_a", email="test_a", password="test", salt=lib.generate_salt())
    user_b = User(name="test_b", email="test_b", password="test", salt=lib.generate_salt())
    event = Event(name="test", starting_money=100, active=True, joinable=True, creator=user_a, allow_self_bets=True)
    round = Round(name="test", event=event, competitor_a=user_a, competitor_b=user_b, odds="2:1", winner=user_b)
    wager = Wager(amount=10, user=user_a, stake=user_b, round=round)
    db.session.add(wager)
    db.session.commit()

    assert wager.get_outcome() == 10