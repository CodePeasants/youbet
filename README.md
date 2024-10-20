# You Bet
This is a flask app for managing wagers and bets.

## Setup
Steps to setup this app for the first time on the server.

1. Create your virtual environment 

2. `pip install -r requirements.txt`

3. Create the flask [configuration file](https://flask.palletsprojects.com/en/3.0.x/config/#configuring-from-python-files). This is a `settings.py` module on the root of the `youbet` package.
You must define the following keys:
- `SQLALCHEMY_DATABASE_URI` (e.g. `sqlite:///data.db`)
- `SECRET_KEY`: This can be generated via: ```python -c "import uuid;print(uuid.uuid4().hex)"```
- `SENDGRID_API_KEY`: This app uses [SendGrid]("www.sendgrid.com") to send emails (e.g. for password reset).
- `RESET_PASSWORD_SENDER_ADDRESS`: The email address that password reset emails will be sent from (e.g. "youbet@domain.com").

The following keys are optional, but recommended:
- `RESET_PASSWORD_MAX_TRIES`: The maximum number of times a user can request a new verification code email before actually resetting their password.
- `MAX_EVENTS_PER_USER`: The maximum number of events a user can have at one time - to prevent flooding the database.
- `MAX_ROUNDS_PER_EVENT`: The maximum number of rounds a single event can have - to prevent flooding the database.

4. I recommend adding the path to the `youbet` repo to the `PYTHONPATH` automatically when you activate your virtual environment.
    - Add a `youbet.pth` file under `venv/lib/pythonX.X/site-packages` with a single line depicting the local path to this repo.

5. Initialize the database via:
    - ```python create_db.py```
    - You can pass the `--rebuild` flag to clear existing database tables if they exist.
    - You can pass the `--test` flag to populate your database with some example data to test the app with (do not use for production db).

6. Run the flask app (e.g. `flask --app youbet/app run`)

## Development
While developing the app, make sure to run in debug mode:
```flask --app youbet/app run --debug```