# You Bet
This is a flask app for managing wagers and bets.

## Setup
Steps to setup this app for the first time on the server.

1. Create your virtual environment 
2. `pip install -r requirements.txt`
3. Create the flask [configuration file](https://flask.palletsprojects.com/en/3.0.x/config/#configuring-from-python-files). This is a `settings.py` module on the root of the `youbet` package.
You must define the following keys:
- `SQLALCHEMY_DATABASE_URI` (e.g. `sqlite:///data.db`)
- `SECRET_KEY`
    - This can be generated via: ```python -c "import uuid;print(uuid.uuid4().hex)"```
4. Initialize the database via:
```python create_db.py```
5. Run the flask app (e.g. `flask --app youbet/app run`)

## Development
While developing the app, make sure to run in debug mode:
```flask --app youbet/app run --debug```