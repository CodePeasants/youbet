from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from functools import partial
from youbet import lib
# from sqlalchemy.dialects.postgresql import UUID
# import uuid


db = SQLAlchemy()
now = partial(datetime.now, timezone.utc)


class Base(db.Model):
    __abstract__ = True


class CompetitorBase(Base):
    __tablename__ = 'competitor_base'
    # Make the ID in this table a UUID as a lazy work-around to make users and competitors interchangable without
    #  accidentally using a user ID with a competitor ID.
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    column_type = db.Column(db.String(50))

    __mapper_args__ = {
        "polymorphic_identity": "competitor_base",
        "with_polymorphic": "*",
        "polymorphic_on": column_type
    }


class User(CompetitorBase, Base):
    __tablename__ = 'user'
    id = db.Column(db.Integer, db.ForeignKey("competitor_base.id"), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    salt = db.Column(db.String(32), nullable=False)
    date_registered = db.Column(db.DateTime, nullable=False, default=now)
    password_reset_code = db.Column(db.Integer, nullable=True, default=None)
    password_reset_tries = db.Column(db.Integer, nullable=False, default=0)

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "with_polymorphic": "*",
    }

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
    allow_self_bets = db.Column(db.Boolean, nullable=False, default=True)
    participants_are_competitors = db.Column(db.Boolean, nullable=False, default=True)
    max_participants = db.Column(db.Integer, nullable=True, default=None)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', foreign_keys=[creator_id])
    participants = db.relationship('User', secondary='event_participant')
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    winner = db.relationship('User', foreign_keys=[winner_id])
    rounds = db.relationship('Round', uselist=True, back_populates='event')
    competitors = db.relationship('Competitor', uselist=True, back_populates='event')

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
            return "bg-success"
        elif status == self.Status.ACTIVE:
            return "bg-primary"
        elif status == self.Status.COMPLETE:
            return "bg-secondary"
        else:
            return "bg-danger"
    
    def get_current_money(self, user):
        if user not in self.participants:
            return 0
        
        delta = 0
        for round in self.rounds:
            for wager in round.wagers:
                if wager.user != user:
                    continue
                delta += wager.get_outcome()
        return self.starting_money + delta

    def get_available_money(self, user, exclude_wager=None):
        if isinstance(user, int):
            user = User.query.filter_by(id=user).first()
        if not user:
            raise RuntimeError("No user: {}".format(user))
        
        current_money = self.get_current_money(user)
        outstanding = 0
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
    
    def get_rounds(self):
        return sorted(self.rounds, key=lambda x: (x.accepting_wagers(), x.date_created), reverse=True)
    
    def get_competitor_record(self, competitor, versus=None):
        if versus is not None:
            rounds = db.session.query(Round).filter(
                ((Round.competitor_a == competitor) | (Round.competitor_b == competitor)) &
                ((Round.competitor_a == versus) | (Round.competitor_b == versus)) &
                (Round.event == self)
            ).all()
        else:
            rounds = db.session.query(Round).filter(
                (Round.competitor_a == competitor) | (Round.competitor_b == competitor) &
                (Round.event == self)
            ).all()
        
        wins = 0
        losses = 0
        for round in rounds:
            if round.winner:
                if round.winner == competitor:
                    wins += 1
                else:
                    losses += 1
        return wins, losses
    
    def get_next_round_name(self):
        return f"Round {len(self.rounds) + 1}"
    
    def get_competitors(self):
        result = []
        result += self.competitors
        if self.participants_are_competitors:
            result += self.participants
        return result

    def get_competitor(self, id):
        return CompetitorBase.query.filter_by(id=id).first()
    

event_participant = db.Table('event_participant',
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Competitor(CompetitorBase, Base):
    __tablename__ = 'competitor'
    id = db.Column(db.Integer, db.ForeignKey("competitor_base.id"), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    event = db.relationship('Event', back_populates='competitors')

    __mapper_args__ = {
        "polymorphic_identity": "competitor",
        "with_polymorphic": "*",
    }

    def __repr__(self):
        return '<Competitor %r>' % self.id


class Round(Base):
    __tablename__ = 'round'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    accept_wagers = db.Column(db.Boolean, nullable=False, default=True)
    odds = db.Column(db.String(30), default="1:1")
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    event = db.relationship('Event', back_populates='rounds')
    winner_id = db.Column(db.Integer, db.ForeignKey('competitor_base.id'))
    winner = db.relationship('CompetitorBase', foreign_keys=[winner_id])
    competitor_a_id = db.Column(db.Integer, db.ForeignKey('competitor_base.id'))
    competitor_a = db.relationship('CompetitorBase', foreign_keys=[competitor_a_id])
    competitor_b_id = db.Column(db.Integer, db.ForeignKey('competitor_base.id'))
    competitor_b = db.relationship('CompetitorBase', foreign_keys=[competitor_b_id])
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
        if not self.accept_wagers or self.winner or self.event.winner:
            return False
        return True
    
    def has_wagered(self, user_id):
        if not isinstance(user_id, int):
            user_id = user_id.id

        for wager in self.wagers:
            if wager.user.id == user_id:
                return True
        return False
    
    def can_wager(self, user_id):
        if self.event.winner:
            return False
        if self.winner:
            return False
        if not self.accepting_wagers:
            return False
        
        competitor_ids = {self.competitor_a_id, self.competitor_b_id}
        if not self.event.allow_self_bets and user_id in competitor_ids:
            return False
        return True


class Wager(Base):
    __tablename__ = 'wager'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=now)
    amount = db.Column(db.Float, nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'))
    round = db.relationship('Round', back_populates='wagers')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', foreign_keys=[user_id])
    stake_id = db.Column(db.Integer, db.ForeignKey('competitor_base.id'))
    stake = db.relationship('CompetitorBase', foreign_keys=[stake_id])

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
    
    @classmethod
    def get_update_wager_route(cls, user, round):
        existing_wager = cls.query.filter_by(round=round, user=user).first()
        if existing_wager:
            return "add_wager"
        else:
            return "edit_wager"
