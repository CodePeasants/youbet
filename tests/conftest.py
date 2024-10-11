import pytest
from flask import Flask
from youbet.database import db as db_model


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_model.init_app(app)


@pytest.fixture(scope="function")
def db():
    with app.app_context():
        db_model.create_all()
        yield db_model
        db_model.session.remove()
        db_model.drop_all()
