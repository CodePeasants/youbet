"""
Useful flask + sqlalchemy CRUD tutorial:
https://www.youtube.com/watch?v=Z1RJmh_OqeA&t=1805s

Sending emails via python **NOTE:** this is an out-of-date doc, but still contains useful info:
https://realpython.com/python-send-email/#including-html-content

Docs:
flask-sqlalchemy: https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/
bootstrap css: https://getbootstrap.com/docs/3.4/css/

TODO
- implement add_wager section of event.html rounds table
    - add a selection for the player and an amount to wager along with the add wager button.
    - When betting closes, this becomes text displaying their wager.
    - Maybe add an option to view & edit your wager on the view round page as well?
- Add option to close betting when editing a round
- make a tool to initialize a DB with some users and participants in an event so I have more options to work with while testing.
- Implement edit event page

- right-align account buttons in navbar (some bootstrap class on the span?).
- fix forgot password email sending, have to use google cloud API.
"""
import os
import ast
from flask import Flask, render_template, session, url_for, redirect, request, flash
from youbet import lib
from youbet.database import db, User, Event, Round, Wager


app = Flask(__name__)
app.config.from_object('youbet.settings')
if "YOUBET_SETTINGS" in os.environ:
    app.config.from_envvar('YOUBET_SETTINGS')
db.init_app(app)


@app.route('/')
def main():
    if not session.get("user"):
        return redirect(url_for('login'))
    else:
        events = Event.query.where(Event.active == True).all()
        events.sort(key=lambda x: (-Event.Status.get_sort_order().index(x.get_status()), x.date_created), reverse=True)
        return render_template('index.html', events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not email or not password:
            flash("Please enter an email and password", "error")
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account with that email exists", "error")
            return redirect(url_for('login'))
        
        if not lib.verify_password(user.password, user.salt, password):
            flash("Incorrect password", "error")
            return redirect(url_for('login'))
        session["user"] = user.to_json()
        return redirect(url_for('main'))
    else:
        return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("user", None)
    flash("You were logged out", "info")
    return redirect(url_for('login'))

@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    if request.method == 'POST':
        email = request.form['email']
        existing_users = User.query.filter_by(email=email).all()
        if len(existing_users) > 0:
            flash("An account with that email already exists", "error")
            return redirect(url_for('add_account'))
        
        name = request.form['name']
        existing_names = User.query.filter_by(name=name).all()
        if len(existing_names) > 0:
            flash("An account with that name already exists", "error")
            return redirect(url_for('add_account'))
        
        password = request.form['password']
        if not password or not lib.validate_password(password):
            flash("Please enter a valid password", "error")
            return redirect(url_for('add_account'))
        
        encrypted_password, salt = lib.hash_password(password, as_str=True)
        new_user = User(name=name, email=email, password=encrypted_password, salt=salt)
        try:
            db.session.add(new_user)
            db.session.commit()
            session["user"] = new_user.to_json()
            return redirect(url_for('main'))
        except Exception as e:
            flash("Something went wrong", "error")
            redirect(url_for('add_account'))
            print(e)
    else:
        return render_template('add_account.html')
    

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account with that email exists", "error")
            return redirect(url_for('forgot_password'))
        
        lib.reset_password(user, db)
        return redirect(url_for('login'))
    else:
        return render_template('forgot_password.html')


@app.route('/account', methods=['GET', 'POST'])
def account():
    user_data = session.get("user")
    if not user_data:
        return redirect(url_for('login'))
    
    session_user = User.from_json(user_data)
    if session_user is None:
        flash("Session user not found in database!", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        change_made = False
        if password:
            encrypted_password, _ = lib.hash_password(password, salt=session_user.salt, as_str=True)
            session_user.password = encrypted_password
            change_made = True
        
        if name != session_user.name:
            session_user.name = name
            change_made = True
        
        if email != session_user.email:
            session_user.email = email
            change_made = True
        
        if change_made:
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                flash("Something went wrong", "error")
            else:
                session["user"] = session_user.to_json()
                flash("Changes saved", "info")
        else:
            flash("No changes made", "info")
        return redirect(url_for('account'))
    else:
        return render_template('account.html', user=session_user)

@app.route('/event/<event_id>', methods=['GET', 'POST'])
def event(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    session_user_id = session.get("user", {}).get("id")
    session_user = User.query.filter_by(id=session_user_id).first()
    user_wagers = db.session.query(Wager).join(Round).join(Event).filter(
        Wager.user == session_user,
        Event.id == event.id
    ).all()
    round_wagers = {}
    for wager in user_wagers:
        round_wagers[wager.round.id] = wager
    
    return render_template('event.html', event=event, session_user=session_user, round_wagers=round_wagers)


@app.route('/add_event', methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        user_data = session.get("user")
        if not user_data:
            flash("You must log in to create an event!", "error")
            return redirect(url_for('login'))
        
        user = User.from_json(user_data)
        if user is None:
            flash("Session user not found in database!", "error")
            return redirect(url_for('login'))
        
        name = request.form['name']
        if not name:
            flash("Please enter a valid name", "error")
            return redirect(url_for('add_event'))
        
        starting_money = request.form['starting_money']
        if not starting_money:
            flash("Please enter a valid starting money", "warning")
            return redirect(url_for('add_event'))

        new_event = Event(name=name, starting_money=starting_money, creator=user)
        try:
            db.session.add(new_event)
            db.session.commit()
            return redirect(url_for('main'))
        except Exception as e:
            flash("Something went wrong", "error")
    else:
        return render_template('add_event.html')

@app.route('/event/<event_id>/edit', methods=['GET', 'POST']) 
def edit_event(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    # TODO
    # return render_template('edit_event.html', event=event)
    return "hello world"

@app.route('/event/<event_id>/remove', methods=['GET', 'POST'])
def remove_event(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "warning")
        return redirect(url_for('main'))
    
    try:
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    return redirect(url_for('main'))

@app.route('/event/<event_id>/remove_user/<user_id>', methods=['GET','POST'])
def remove_event_user(event_id, user_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for('event', event_id=event_id))
    
    try:
        event.participants.remove(user)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
        return redirect(url_for('event', event_id=event_id))
    return redirect(url_for('event', event_id=event_id))


@app.route('/event/<event_id>/add_user/<user_id>', methods=['GET', 'POST'])
def add_event_user(event_id, user_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for('event', event_id=event_id))
    
    try:
        event.participants.append(user)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
        return redirect(url_for('event', event_id=event_id))
    return redirect(url_for('event', event_id=event_id))


@app.route('/event/<event_id>/round/<round_id>', methods=['GET', 'POST'])
def round(event_id, round_id):
    round = Round.query.filter_by(id=round_id).first()
    if not round:
        flash("Round not found", "error")
        return redirect(url_for('event', event_id=event_id))
    
    session_user = User.query.filter_by(id=session.get("user", {}).get('id')).first()
    
    return render_template('round.html', round=round, session_user=session_user)


@app.route("/event/<event_id>/add_round", methods=['GET', 'POST'])
def add_round(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))

    if request.method == 'POST':
        name = request.form['name']
        if not name:
            flash("Please enter a valid name", "warning")
            return redirect(url_for('add_round', event_id=event_id))
        
        odds = request.form['odds']
        if odds and not lib.validate_odds(odds):
            flash("Please enter a valid odds", "warning")
            return redirect(url_for('add_round', event_id=event_id))
        if not odds:
            odds = "1:1"
        
        player_a = User.query.filter_by(id=request.form['player_a']).first()
        if not player_a:
            flash("Player A not found", "error")
            return redirect(url_for('add_round', event_id=event_id))
        
        player_b = User.query.filter_by(id=request.form['player_b']).first()
        if not player_b:
            flash("Player B not found", "error")
            return redirect(url_for('add_round', event_id=event_id))

        new_round = Round(name=name, event=event, odds=odds, competitor_a=player_a, competitor_b=player_b)
        try:
            db.session.add(new_round)
            db.session.commit()
            return redirect(url_for('event', event_id=event_id))
        except Exception as e:
            print(e)
            flash("Something went wrong", "error")
            return redirect(url_for('add_round', event_id=event_id))
    else:
        return render_template('add_round.html', event=event)


@app.route('/event/<event_id>/round/<round_id>/edit', methods=['GET', 'POST'])
def edit_round(event_id, round_id):
    round = Round.query.filter_by(id=round_id).first()
    if not round:
        flash("Round not found", "error")
        return redirect(url_for('event', event_id=event_id))

    if request.method == 'POST':
        name = request.form['name']
        if not name:
            flash("Please enter a valid name", "warning")
            return redirect(url_for('edit_round', event_id=event_id, round_id=round_id))
        
        odds = request.form['odds']
        if not odds or not lib.validate_odds(odds):
            flash("Please enter a valid odds", "warning")
            return redirect(url_for('edit_round', event_id=event_id, round_id=round_id))
        
        player_a = User.query.filter_by(id=request.form['player_a']).first()
        if not player_a:
            flash("Player A not found", "error")
            return redirect(url_for('edit_round', event_id=event_id, round_id=round_id))
        
        player_b = User.query.filter_by(id=request.form['player_b']).first()
        if not player_b:
            flash("Player B not found", "error")
            return redirect(url_for('edit_round', event_id=event_id, round_id=round_id))
        
        accept_wagers = lib.coerce_str_to_bool(request.form.get("accept_wagers"))
        winner = User.query.filter_by(id=request.form['winner']).first()

        changed = False
        if name != round.name:
            round.name = name
            changed = True
        if odds != round.odds:
            round.odds = odds
            changed = True
        if player_a != round.competitor_a:
            round.competitor_a = player_a
            changed = True
        if player_b != round.competitor_b:
            round.competitor_b = player_b
            changed = True
        if winner != round.winner:
            round.winner = winner
            changed = True
        if accept_wagers != round.accept_wagers:
            round.accept_wagers = accept_wagers
            changed = True

        if changed:
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                flash("Something went wrong", "error")
                return redirect(url_for('edit_round', event_id=event_id, round_id=round_id))
        return redirect(url_for('round', event_id=event_id, round_id=round_id))
    else:
        return render_template('edit_round.html', round=round)

@app.route('/event/<event_id>/round/<round_id>/remove', methods=['GET', 'POST'])
def remove_round(event_id, round_id):
    round = Round.query.filter_by(id=round_id).first()
    if not round:
        flash("Round not found", "warning")
        return redirect(url_for('event', event_id=event_id))
    
    try:
        db.session.delete(round)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    return redirect(url_for('event', event_id=event_id))


@app.route('/event/<event_id>/round/<round_id>/add_wager', methods=['GET', 'POST'])
def add_wager(event_id, round_id):
    round = Round.query.filter_by(id=round_id).one()
    if not round:
        flash("Round not found", "error")
        return redirect(url_for('event', event_id=event_id))
    
    user_id = session.get("user", {}).get("id")
    if not user_id:
        flash("Not logged in!", "error")
        return redirect(url_for('event', event_id=event_id))

    user = User.query.filter_by(id=user_id).one()
    if not user:
        flash(f"User ID: {user_id} not found!", "error")
        return redirect(url_for('event', event_id=event_id))
    
    stake = User.query.filter_by(id=request.form["stake"]).one()
    if not stake:
        flash(f"User ID: {stake} not found!", "error")
        return redirect(url_for('event', event_id=event_id))
    
    amount = request.form["amount"]
    # If they submit a bid of 0, remove their wager.
    if not amount or float(amount) <= 0:
        existing_wager = Wager.query.filter_by(user=user, round=round).first()
        if not existing_wager:
            flash("No wager set.", "info")
            return redirect(url_for('event', event_id=event_id))
        return redirect(url_for('remove_wager', event_id=round.event.id, round_id=round.id, wager_id=existing_wager.id))
    else:
        amount = float(amount)

    new_wager = Wager(amount=amount, round=round, user=user, stake=stake)
    try:
        db.session.add(new_wager)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    
    return redirect(url_for('event', event_id=event_id))

@app.route('/event/<event_id>/round/<round_id>/wager/<wager_id>/remove', methods=['GET', 'POST'])
def remove_wager(event_id, round_id, wager_id):
    wager = Wager.query.filter_by(id=wager_id).first()
    if not wager:
        flash("Wager not found", "warning")
        return redirect(url_for('event', event_id=event_id))
    try:
        db.session.delete(wager)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    flash("Wager removed.", "info")
    return redirect(url_for('event', event_id=event_id))


if __name__ == '__main__':
    app.run()
