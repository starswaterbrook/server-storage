import os
import sys
import shutil

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)
from tests.conftest import client, UPLOAD_DIR, TEST_FILE_NAME


def test_download(client):
    with client.session_transaction() as session:
        user_id = session["id"]
        path = f"{UPLOAD_DIR}/{user_id}/{TEST_FILE_NAME}"

    with open(path, "w") as file:
        file.write("Test")

    response = client.get(f"/download/{TEST_FILE_NAME}")
    response.close()

    file_exists = os.path.isfile(path)
    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 200
    assert file_exists == 1


def test_download_invalid(client):
    with client.session_transaction() as session:
        response = client.get("/download/not_dummy.txt")
        user_id = session["id"]

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 404
