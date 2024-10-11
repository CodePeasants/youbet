from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from functools import partial
from youbet import lib


db = SQLAlchemy()
now = partial(datetime.now, timezone.utc)


class Base(db.Model):
    __abstract__ = True


class User(Base):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    date_registered = db.Column(db.DateTime, nullable=False, default=now)
    events_created = db.relationship('Event', back_populates='creator', uselist=True)
    events_participated = db.relationship('Event', secondary='event_participant', back_populates='participants')

    def __repr__(self):
        return '<User %r>' % self.id
    
    def to_json(self):
        return {"id": self.id, "name": self.name, "email": self.email}
    
    @classmethod
    def from_json(cls, data):
        return User.query.filter_by(id=data["id"]).first()
    

class Event(Base):
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

    class Status:
        COMPLETE = "Complete"
        OPEN = "Open"
        ACTIVE = "Active"
        CLOSED = "Closed"

        @classmethod
        def get_sort_order(cls):
            return [cls.OPEN, cls.ACTIVE, cls.COMPLETE, cls.CLOSED]

    def __repr__(self):
        return '<Event %r>' % self.id
    
    def get_status(self):
        if self.winner:
            return self.Status.COMPLETE
        elif self.joinable:
            return self.Status.OPEN
        elif self.active:
            return self.Status.ACTIVE
        else:
            return self.Status.CLOSED

    def get_status_class(self):
        status = self.get_status()
        if status == self.Status.OPEN:
            return "text-success"
        elif status == self.Status.ACTIVE:
            return "text-primary"
        elif status == self.Status.COMPLETE:
            return "text-secondary"
        else:
            return "text-danger"
    
    def get_current_money(self, user):
        if user not in self.participants:
            return 0
        
        delta = 0
        for round in self.rounds:
            for wager in round.wagers:
                delta += wager.get_outcome()
        return self.starting_money + delta

    def get_available_money(self, user, exclude_wager=None):
        if isinstance(user, int):
            user = User.query.filter_by(id=user).first()
        if not user:
            raise RuntimeError("No user: {}".format(user))
        
        current_money = self.get_current_money(user)
        outstanding = 0
        # wagers = Wager.query.filter_by(user=user, event=self).all()
        wagers = db.session.query(Wager).join(Round).join(Event).filter(
            Wager.user == user,
            Event.id == self.id
        ).all()
        for wager in wagers:
            if exclude_wager is not None and wager.id == exclude_wager.id:
                continue
            if wager.get_status() == Wager.Status.UNDECIDED:
                outstanding += wager.amount
        return current_money - outstanding

    def get_participant_ids(self):
        return [x.id for x in self.participants]
    
    def get_participants(self):
        if not self.participants:
            return []
        return sorted(self.participants, key=self.get_current_money)
    

event_participant = db.Table('event_participant',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

event_winner = db.Table('event_winner',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Round(Base):
    __tablename__ = 'round'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    accept_wagers = db.Column(db.Boolean, nullable=False, default=True)
    odds = db.Column(db.String(30), default="1:1")
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    event = db.relationship('Event', back_populates='rounds')
    winner = db.relationship('User', secondary="round_winner", uselist=False)
    competitor_a = db.relationship('User', secondary="competitor_a", uselist=False)
    competitor_b = db.relationship('User', secondary="competitor_b", uselist=False)
    wagers = db.relationship('Wager', uselist=True, back_populates='round')

    def __repr__(self):
        return '<Round %r>' % self.id
    
    def get_wager(self, user):
        if isinstance(user, int):
            user = User.query.filter_by(id=user).first()
        if not user:
            return
        for wager in self.wagers:
            if wager.user == user:
                return wager
    
    def get_odds(self):
        if self.odds:
            return self.odds.split(":")
        return ("", "")
    
    def accepting_wagers(self):
        if not self.accept_wagers or self.winner:
            return False
        return True


competitor_a = db.Table('competitor_a',
    db.Column('round_id', db.Integer, db.ForeignKey('round.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

competitor_b = db.Table('competitor_b',
    db.Column('round_id', db.Integer, db.ForeignKey('round.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

round_winner = db.Table('round_winner',
    db.Column('round_id', db.Integer, db.ForeignKey('round.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Wager(Base):
    __tablename__ = 'wager'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    amount = db.Column(db.Float, nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    round = db.relationship('Round', back_populates='wagers')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id])
    stake_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    stake = db.relationship('User', foreign_keys=[stake_id])

    class Status:
        UNDECIDED = "undecided"
        WIN = "win"
        LOSE = "lose"

    def __repr__(self):
        return '<Wager %r>' % self.id
    
    def get_outcome(self):
        if not self.round.winner:
            return 0

        if self.round.winner == self.stake:
            return lib.solve_odds(self.round.odds, self.amount, reverse_odds=self.round.competitor_b == self.stake)
        else:
            return -self.amount
    
    def get_status(self):
        outcome = self.get_outcome()
        if outcome == 0:
            return self.Status.UNDECIDED
        elif outcome > 0:
            return self.Status.WIN
        else:
            return self.Status.LOSE

    def get_status_class(self, status=None):
        if status is None:
            status = self.get_status()

        if status == self.Status.UNDECIDED:
            return "text-info"
        elif status == self.Status.WIN:
            return "text-success"
        elif status == self.Status.LOSE:
            return "text-danger"
        else:
            return "text-primary"
