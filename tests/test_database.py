
from youbet.database import User, Event, Round, Competitor, Wager
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
    assert event in user.events_created


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


def test_competitor(db):
    user = User(name="test", email="test", password="test", salt=lib.generate_salt())
    event = Event(name="test", starting_money=100, active=True, joinable=True, creator=user)
    round = Round(name="test", event=event)
    competitor = Competitor(odds=1.0, user=user, round=round)
    db.session.add(competitor)
    db.session.commit()

    round_trip = db.session.get(Competitor, competitor.id)
    round_trip == competitor

    assert competitor.user == user
    assert competitor.round == round

def test_wager(db):
    user = User(name="test", email="test", password="test", salt=lib.generate_salt())
    event = Event(name="test", starting_money=100, active=True, joinable=True, creator=user)
    round = Round(name="test", event=event)
    competitor = Competitor(odds=1.0, user=user, round=round)
    wager = Wager(amount=1.0, user=user, competitor=competitor, round=round)
    db.session.add(wager)
    db.session.commit()

    round_trip = db.session.get(Wager, wager.id)
    round_trip == wager

    assert wager.user == user
    assert wager.competitor == competitor
    assert wager.round == round