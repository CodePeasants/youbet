"""
Useful flask + sqlalchemy CRUD tutorial:
https://www.youtube.com/watch?v=Z1RJmh_OqeA&t=1805s

Sending emails via python **NOTE:** this is an out-of-date doc, but still contains useful info:
https://realpython.com/python-send-email/#including-html-content

Docs:
flask-sqlalchemy: https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/
bootstrap: https://getbootstrap.com/docs/5.0/forms/overview/
bootstrap icons: https://icons.getbootstrap.com/
"""
import os
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
    i_email = request.args.get("i_email")
    if request.method == 'POST':
        email = request.form['email']
        if not email:
            flash("Please enter an email", "warning")
            return redirect(url_for('login'))
        
        password = request.form['password']
        if not password:
            flash("Please enter a password", "warning")
            return redirect(url_for('login', i_email=email))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account with that email exists", "error")
            return redirect(url_for('login'))
        
        if not lib.verify_password(user.password, user.salt, password):
            flash("Incorrect password", "warning")
            return redirect(url_for('login', i_email=email))
        
        session["user"] = user.to_json()
        return redirect(url_for('main'))
    else:
        return render_template('login.html', i_email=i_email)


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
            return redirect(url_for("main"))
        except Exception as e:
            flash("Something went wrong", "error")
            redirect(url_for('add_account'))
            print(e)
    else:
        return render_template('add_account.html')
    

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    i_email = request.args.get("i_email")
    i_code = request.args.get("i_code")

    if request.method == 'POST':
        email = request.form['email']
        if not email:
            flash(f"You must enter an email", "error")
            return redirect(url_for('forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash(f"No account with that email: {email} exists", "error")
            return redirect(url_for('forgot_password'))

        if request.form['submit_button'] == "send_code":
            max_reset_tries = app.config.get("RESET_PASSWORD_MAX_TRIES")
            if max_reset_tries and user.password_reset_tries >= max_reset_tries:
                flash(f"You have exceeded the maximum number of verification code sends ({max_reset_tries}) before changing your password.", "error")
                return redirect(url_for('forgot_password', i_email=email))

            success = lib.reset_password(user, db)
            if not success:
                flash("Something went wrong.", "error")
                return redirect(url_for('forgot_password'))
            
            flash("Verification code sent.", "info")
            return redirect(url_for('forgot_password', i_email=email))
        
        verification_code = request.form["code"]
        if int(verification_code) != user.password_reset_code:
            flash("Invalid verification code", "warning")
            return redirect(url_for('forgot_password', i_email=email, i_code=verification_code))

        new_password = request.form['new_password']
        if not new_password or not lib.validate_password(new_password):
            flash("Please enter a valid password", "error")
            return redirect(url_for('forgot_password', i_email=email, i_code=verification_code))
        
        encrypted_password, salt = lib.hash_password(new_password, as_str=True)
        
        try:
            user.password = encrypted_password
            user.salt = salt
            user.password_reset_code = None
            user.password_reset_tries = 0
            db.session.commit()
            return redirect(url_for("login"))
        except Exception as e:
            flash("Something went wrong", "error")
            print(e)
            return redirect(url_for('forgot_password', i_email=email, i_code=verification_code))
    else:
        return render_template('forgot_password.html', i_email=i_email, i_code=i_code)


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
        return redirect(lib.get_redirect_url())
    else:
        return render_template('account.html', user=session_user)

@app.route('/event/<event_id>', methods=['GET', 'POST'])
def event(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(lib.get_redirect_url())
    
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
        
        max_events = app.config.get("MAX_EVENTS_PER_USER")
        if max_events:
            user_events = Event.query.filter_by(creator=user).all()
            if len(user_events) >= max_events:
                flash(f"You have already created the maximum number of allowed events ({max_events})! Delete an event to make a new one.", "error")
                return redirect(url_for('add_event'))
        
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
            return redirect(lib.get_redirect_url())
        except Exception as e:
            flash("Something went wrong", "error")
    else:
        return render_template('add_event.html')

@app.route('/event/<event_id>/edit', methods=['GET', 'POST']) 
def edit_event(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(lib.get_redirect_url())
    
    if request.method == "POST":
        name = request.form["name"]
        if not name:
            flash("Please enter a valid name", "warning")
            return redirect(url_for('edit_event', event_id=event.id))
        
        starting_money = request.form["starting_money"]
        if not starting_money or float(starting_money) <= 0:
            flash("Please enter a valid starting money", "warning")
            return redirect(url_for('edit_event', event_id=event.id))
        
        joinable = lib.coerce_str_to_bool(request.form.get("joinable"))
        winner = User.query.filter_by(id=request.form["winner"]).first()

        change_made = False
        if name != event.name:
            event.name = name
            change_made = True
        
        if starting_money != event.starting_money:
            event.starting_money = starting_money
            change_made = True
        
        if joinable != event.joinable:
            event.joinable = joinable
            change_made = True
        
        if winner != event.winner:
            event.winner = winner
            change_made = True
        
        if change_made:
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                flash("Something went wrong", "error")
        else:
            flash("No changes made", "info")
        return redirect(lib.get_redirect_url())
    else:
        session_user = User.query.filter_by(id=session.get("user", {}).get('id')).first()
        return render_template('edit_event.html', event=event, session_user=session_user)


@app.route('/event/<event_id>/remove', methods=['GET', 'POST'])
def remove_event(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "warning")
        return redirect(lib.get_redirect_url())
    
    try:
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    return redirect(url_for("main"))


@app.route('/event/<event_id>/remove_user/<user_id>', methods=['GET','POST'])
def remove_event_user(event_id, user_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(lib.get_redirect_url())
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found", "error")
        return redirect(lib.get_redirect_url())
    
    try:
        event.participants.remove(user)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    return redirect(lib.get_redirect_url())


@app.route('/event/<event_id>/add_user/<user_id>', methods=['GET', 'POST'])
def add_event_user(event_id, user_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(lib.get_redirect_url())
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found", "error")
        return redirect(lib.get_redirect_url())
    
    try:
        event.participants.append(user)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    return redirect(lib.get_redirect_url())


@app.route('/event/<event_id>/round/<round_id>', methods=['GET', 'POST'])
def round(event_id, round_id):
    round = Round.query.filter_by(id=round_id).first()
    if not round:
        flash("Round not found", "error")
        return redirect(lib.get_redirect_url())
    
    session_user = User.query.filter_by(id=session.get("user", {}).get('id')).first()
    
    return render_template('round.html', event=round.event, round=round, session_user=session_user)


@app.route("/event/<event_id>/add_round", methods=['GET', 'POST'])
def add_round(event_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(lib.get_redirect_url())
    
    if request.method == 'POST':
        max_rounds = app.config.get("MAX_ROUNDS_PER_EVENT")
        if max_rounds:
            if len(event.rounds) >= max_rounds:
                flash(f"You have already created the maximum number of allowed rounds ({max_rounds})!.", "error")
                return redirect(url_for('add_round', event_id=event.id))

        name = request.form['name']
        if not name:
            flash("Please enter a valid name", "warning")
            return redirect(url_for("add_round", event_id=event.id))
        
        odds = request.form['odds']
        if odds and not lib.validate_odds(odds):
            flash("Please enter a valid odds", "warning")
            return redirect(url_for("add_round", event_id=event.id))
        if not odds:
            odds = "1:1"
        
        player_a = User.query.filter_by(id=request.form['player_a']).first()
        if not player_a:
            flash("Player A not found", "error")
            return redirect(url_for("add_round", event_id=event.id))
        
        player_b = User.query.filter_by(id=request.form['player_b']).first()
        if not player_b:
            flash("Player B not found", "error")
            return redirect(url_for("add_round", event_id=event.id))

        new_round = Round(name=name, event=event, odds=odds, competitor_a=player_a, competitor_b=player_b)
        try:
            db.session.add(new_round)
            db.session.commit()
            return redirect(url_for('event', event_id=event_id))
        except Exception as e:
            print(e)
            flash("Something went wrong", "error")
            return redirect(lib.get_redirect_url())
    else:
        session_user = User.query.filter_by(id=session.get("user", {}).get('id')).first()
        return render_template('add_round.html', event=event, session_user=session_user)


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
        return redirect(lib.get_redirect_url())
    else:
        session_user = User.query.filter_by(id=session.get("user", {}).get('id')).first()
        return render_template('edit_round.html', event=round.event, round=round, session_user=session_user)

@app.route('/event/<event_id>/round/<round_id>/remove', methods=['GET', 'POST'])
def remove_round(event_id, round_id):
    round = Round.query.filter_by(id=round_id).first()
    if not round:
        flash("Round not found", "warning")
        return redirect(lib.get_redirect_url())
    
    try:
        db.session.delete(round)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    return redirect(lib.get_redirect_url())


@app.route('/event/<event_id>/round/<round_id>/add_wager', methods=['GET', 'POST'])
def add_wager(event_id, round_id):
    round = Round.query.filter_by(id=round_id).one()
    if not round:
        flash("Round not found", "error")
        return redirect(lib.get_redirect_url())
    
    user_id = session.get("user", {}).get("id")
    if not user_id:
        flash("Not logged in!", "error")
        return redirect(lib.get_redirect_url())

    user = User.query.filter_by(id=user_id).one()
    if not user:
        flash(f"User ID: {user_id} not found!", "error")
        return redirect(lib.get_redirect_url())
    
    stake = User.query.filter_by(id=request.form["stake"]).one()
    if not stake:
        flash(f"User ID: {stake} not found!", "error")
        return redirect(lib.get_redirect_url())
    
    amount = request.form["amount"]
    # If they submit a bid of 0, remove their wager.
    if not amount or float(amount) <= 0:
        existing_wager = Wager.query.filter_by(user=user, round=round).first()
        if not existing_wager:
            flash("No wager set.", "info")
            return redirect(lib.get_redirect_url())
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
    
    return redirect(lib.get_redirect_url())

@app.route('/event/<event_id>/round/<round_id>/edit_wager', methods=['GET', 'POST'])
def edit_wager(event_id, round_id):
    round = Round.query.filter_by(id=round_id).one()
    if not round:
        flash("Round not found", "error")
        return redirect(lib.get_redirect_url())
    
    session_user = User.query.filter_by(id=session.get("user", {}).get('id')).first()
    if not session_user:
        flash("Not logged in!", "error")
        return redirect(lib.get_redirect_url())

    existing_wager = Wager.query.filter_by(user=session_user, round=round).first()
    if not existing_wager:
        flash(f"Existing Wager not found!", "error")
        return redirect(lib.get_redirect_url())

    stake = User.query.filter_by(id=request.form["stake"]).one()
    if not stake:
        flash(f"User ID: {stake} not found!", "error")
        return redirect(lib.get_redirect_url())
    
    # If they submit a bid of 0, remove their wager.
    amount = request.form["amount"]
    if not amount or float(amount) <= 0:
        return redirect(url_for('remove_wager', event_id=round.event.id, round_id=round.id, wager_id=existing_wager.id))
    else:
        amount = float(amount)

    changed = False
    if stake != existing_wager.stake:
        changed = True
        existing_wager.stake = stake
    
    if amount != existing_wager.amount:
        changed = True
        existing_wager.amount = amount

    if changed:
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            flash("Something went wrong", "error")
    
    return redirect(lib.get_redirect_url())

@app.route('/event/<event_id>/round/<round_id>/wager/<wager_id>/remove', methods=['GET', 'POST'])
def remove_wager(event_id, round_id, wager_id):
    wager = Wager.query.filter_by(id=wager_id).first()
    if not wager:
        flash("Wager not found", "warning")
        return redirect(lib.get_redirect_url())
    try:
        db.session.delete(wager)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
    flash("Wager removed.", "info")
    return redirect(lib.get_redirect_url())


if __name__ == '__main__':
    app.run()
