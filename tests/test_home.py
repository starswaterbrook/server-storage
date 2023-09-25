import os
import sys
import shutil

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)
from app import app, File
from mock_client_setup import client, UPLOAD_DIR


def test_home(client):
    with client.session_transaction() as session:
        user_id = session["id"]
        name = session["name"]
    with app.app_context():
        filedata = File.query.filter(File.user_id == user_id).all()

    f_list = [d.file_name for d in filedata]
    response = client.get("/")

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert name.encode("utf-8") in response.data
    assert f_list[0].encode("utf-8") in response.data
