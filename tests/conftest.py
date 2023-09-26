import pytest
import os
import sys
import shutil

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.insert(0, parent_dir)
from app import app, db, User, File
import uuid

script_directory = os.path.dirname(__file__)
os.chdir(script_directory)

UPLOAD_DIR = os.path.abspath("./test_files")
TEST_FILE_NAME = "testfile.txt"
TEST_FILE_DIR = f"{UPLOAD_DIR}/{TEST_FILE_NAME}"


@pytest.fixture
def client():
    if not os.path.isdir(UPLOAD_DIR):
        os.mkdir(UPLOAD_DIR)
        with open(TEST_FILE_DIR, "w") as file:
            file.write("Test")
    app.config["TESTING"] = True
    app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
    app.config["SESSION_COOKIE_NAME"] = "google-login-session"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.secret_key = "test"

    with app.test_client() as client:
        with app.app_context():
            user_id = str(uuid.uuid4())
            db.create_all()
            user = User(user_id, "test")
            file = File(TEST_FILE_NAME, user_id)
            os.mkdir(f"{UPLOAD_DIR}/{user_id}")
            db.session.add(user)
            db.session.add(file)
            db.session.commit()

        with client.session_transaction() as session:
            session["id"] = user_id
            session["name"] = "test"

        yield client


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(UPLOAD_DIR)
