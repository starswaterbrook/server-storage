import os
import sys
import shutil
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from Client import client, UPLOAD_DIR, TEST_FILE_DIR

def test_upload(client):
    with client.session_transaction() as session:
        user_id = session['id']

    with open(TEST_FILE_DIR, 'rb') as file:
        file_data = {'file': (file, 'dummy.txt')}
        response = client.post('/', data=file_data, content_type='multipart/form-data')

    file_created = os.path.isfile(f"{UPLOAD_DIR}/{user_id}/dummy.txt")

    shutil.rmtree(f"{UPLOAD_DIR}/{user_id}")

    assert response.status_code == 302
    assert response.headers.get('Location') == '/'
    assert file_created == 1




