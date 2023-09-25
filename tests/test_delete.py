import os
import sys
import shutil
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from Client import client, UPLOAD_DIR

def test_delete(client):
    with client.session_transaction() as session:
        response = client.post('/delete/dummy.txt')
        user_id = session['id']

    file_exists = os.path.isfile(f"{UPLOAD_DIR}/{user_id}/dummy.txt")

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 200
    assert file_exists == 0