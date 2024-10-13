from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from functools import partial


db = SQLAlchemy()
now = partial(datetime.now, timezone.utc)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    salt = db.Column(db.String(256), nullable=False)
    date_registered = db.Column(db.DateTime, nullable=False, default=now)
    events_created = db.relationship('Event', back_populates='creator', uselist=True)
    events_participated = db.relationship('Event', secondary='event_participant', back_populates='participants')

    def __repr__(self):
        return '<User %r>' % self.id

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    starting_money = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    joinable = db.Column(db.Boolean, nullable=False, default=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', back_populates='events_created')
    participants = db.relationship('User', secondary='event_participant', back_populates='events_participated')
    winner = db.relationship('User', secondary="event_winner")
    rounds = db.relationship('Round', uselist=True, back_populates='event')

    def __repr__(self):
        return '<Event %r>' % self.id


event_participant = db.Table('event_participant',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

event_winner = db.Table('event_winner',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Round(db.Model):
    __tablename__ = 'round'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    accept_wagers = db.Column(db.Boolean, nullable=False, default=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    event = db.relationship('Event', back_populates='rounds')
    winner = db.relationship('User', secondary="round_winner")
    competitors = db.relationship('Competitor', uselist=True, back_populates='round')
    wagers = db.relationship('Wager', uselist=True, back_populates='round')

    def __repr__(self):
        return '<Round %r>' % self.id


round_winner = db.Table('round_winner',
    db.Column('round_id', db.Integer, db.ForeignKey('round.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class Competitor(db.Model):
    __tablename__ = 'competitor'
    id = db.Column(db.Integer, primary_key=True)
    odds = db.Column(db.Float, nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    round = db.relationship('Round', back_populates='competitors')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')

    def __repr__(self):
        return '<Competitor %r>' % self.id


class Wager(db.Model):
    __tablename__ = 'wager'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    amount = db.Column(db.Float, nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    round = db.relationship('Round', back_populates='wagers')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor.id'))
    competitor = db.relationship('Competitor')

    def __repr__(self):
        return '<Wager %r>' % self.id