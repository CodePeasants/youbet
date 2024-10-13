"""
Useful flask + sqlalchemy CRUD tutorial:
https://www.youtube.com/watch?v=Z1RJmh_OqeA&t=1805s

Sending emails via python **NOTE:** this is an out-of-date doc, but still contains useful info:
https://realpython.com/python-send-email/#including-html-content

Docs:
flask-sqlalchemy: https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/
bootstrap css: https://getbootstrap.com/docs/3.4/css/

TODO
- continue working on user system
    - make unit tests for lib.py
    - round.html's add competitor form is super sketchy, it wont work - need to redo that.
    - right-align account buttons in navbar (some bootstrap class on the span?).
    - fix forgot password email sending, have to use google cloud API.
"""
import os
from flask import Flask, render_template, session, url_for, redirect, request, flash
from youbet import lib
from youbet.database import db, User, Event, Round, Competitor, Wager


app = Flask(__name__)
app.config.from_object('settings')
if "YOUBET_SETTINGS" in os.environ:
    app.config.from_envvar('YOUBET_SETTINGS')
db.init_app(app)


@app.route('/')
def main():
    if not session.get("user"):
        return redirect(url_for('login'))
    else:
        events = Event.query.where(Event.active == True).order_by(Event.date_created.desc()).all()
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
        if not lib.check_password(user, password):
            flash("Incorrect password", "error")
            return redirect(url_for('login'))
        session["user"] = user
        return redirect(url_for('/'))
    else:
        return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("user", None)
    flash("You were logged out", "info")
    return redirect(url_for('login'))

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        email = request.form['email']
        existing_users = User.query.filter_by(email=email).all()
        if len(existing_users) > 0:
            flash("An account with that email already exists", "error")
            return redirect(url_for('create_account'))
        
        name = request.form['name']
        existing_names = User.query.filter_by(name=name).all()
        if len(existing_names) > 0:
            flash("An account with that name already exists", "error")
            return redirect(url_for('create_account'))
        
        password = request.form['password']
        if not password:
            flash("Please enter a password", "error")
            return redirect(url_for('create_account'))
        
        new_user = User(name=name, email=email, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            session["user"] = new_user
            return redirect(url_for('account'))
        except Exception as e:
            flash("Something went wrong", "error")
            redirect(url_for('create_account'))
            print(e)
    else:
        return render_template('create_account.html')


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
    if not session.get("user"):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        change_made = False
        if password:
            encrypted_password = lib.hash_password(password)
            session["user"].password = encrypted_password
            change_made = True
        
        if name != session["user"].name:
            session["user"].name = name
            change_made = True
        
        if email != session["user"].email:
            session["user"].email = email
            change_made = True
        
        if change_made:
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                flash("Something went wrong", "error")
                return redirect(url_for('account'))
    else:
        return render_template('account.html')

@app.route('/event/<id>', methods=['GET', 'POST'])
def event(id):
    event = Event.query.filter_by(id=id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    return render_template('event.html', event=event)

@app.route('/event/<event_id>/remove_user/<user_id>', methods=['POST'])
def remove_event_user(event_id, user_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for('event', id=event_id))
    
    try:
        event.users.remove(user)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
        return redirect(url_for('event', id=event_id))
    return redirect(url_for('event', id=event_id))


@app.route('/event/<event_id>/add_user/<user_id>', methods=['POST'])
def add_event_user(event_id, user_id):
    event = Event.query.filter_by(id=event_id).first()
    if not event:
        flash("Event not found", "error")
        return redirect(url_for('main'))
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("User not found", "error")
        return redirect(url_for('event', id=event_id))
    
    try:
        event.users.append(user)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
        return redirect(url_for('event', id=event_id))
    return redirect(url_for('event', id=event_id))


@app.route('/event/<event_id>/round/<id>', methods=['GET', 'POST'])
def round(event_id, round_id):
    round = Round.query.filter_by(id=round_id).first()
    if not round:
        flash("Round not found", "error")
        return redirect(url_for('event', id=event_id))
    
    return render_template('round.html', round=round)


@app.route('/event/<event_id>/round/<round_id>/delete_competitor/<competitor_id>', methods=['POST'])
def delete_competitor(event_id, round_id, competitor_id):
    competitor = Competitor.query.filter_by(id=competitor_id).first()
    if not competitor:
        flash("Competitor not found", "error")
        return redirect(url_for('round', event_id=event_id, round_id=round_id))
    
    try:
        round.competitors.remove(competitor)
        db.session.commit()
    except Exception as e:
        print(e)
        flash("Something went wrong", "error")
        return redirect(url_for('round', event_id=event_id, round_id=round_id))
    return redirect(url_for('round', event_id=event_id, round_id=round_id))


if __name__ == '__main__':
    app.run()
