import os
import sys
import shutil

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)
from mock_client_setup import client, UPLOAD_DIR


def test_logout(client):
    with client.session_transaction() as session:
        user_id = session["id"]
    response = client.get("/logout")
    with client.session_transaction() as session:
        id_cleared = not session.get("id")
        name_cleared = not session.get("name")

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 302
    assert response.headers.get("Location") == "/"
    assert id_cleared == 1
    assert name_cleared == 1
