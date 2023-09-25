import os
import sys
import shutil

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)
from mock_client_setup import client, UPLOAD_DIR, TEST_FILE_NAME


def test_delete(client):
    with client.session_transaction() as session:
        user_id = session["id"]
        with open(f"{UPLOAD_DIR}/{user_id}/{TEST_FILE_NAME}", "w") as file:
            file.write("Test")
        response = client.post(f"/delete/{TEST_FILE_NAME}")

    file_exists = os.path.isfile(f"{UPLOAD_DIR}/{user_id}/{TEST_FILE_NAME}")

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 302
    assert response.headers.get("Location") == "/"
    assert file_exists == 0


def test_delete_invalid(client):
    with client.session_transaction() as session:
        response = client.post("/delete/not_dummy.txt")
        user_id = session["id"]

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 404
