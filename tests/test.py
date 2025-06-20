import sys
import os
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, get_db_connection
import app as app_module

def false_getImages():
    return [("http://test.url/test.jpg", "test.jpg")]

@pytest.fixture(autouse=True)
def patch_getImages(monkeypatch):
    monkeypatch.setattr(app_module, "getImages", false_getImages)


@pytest.fixture
def client():
    os.environ["DB_NAME"] = os.environ.get("TEST_DB_NAME", "test_db") # defaults to 'test_db'
    app.config['TESTING'] = True
    with app.test_client() as client:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('DELETE * FROM memes;')
        connection.commit()
        cursor.close()
        connection.close()
    yield client

def count_memes():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(*) FROM memes;')
    # Unpack the tuple
    (count, ) = cursor.fetchone()
    cursor.close()
    connection.close()
    return count

def get_meme_by_name(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM memes WHERE name = %s', (name, ))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result

def test_add_meme(client):
    # Assert empty table
    assert count_memes() == 0
    response = client.get('/add', follow_redirects = True)
    assert response.status_code == 200
    meme = get_meme_by_name("test.jpg")
    assert meme is not None
    assert meme['url'] == 'http://test.url/test.jpg'
    assert count_memes() == 1

def test_remove_meme(client):
    # Add a meme to be deleted
    response = client.get('/add', follow_redirects = True)
    assert response.status_code == 200
    meme = get_meme_by_name('test.jpg')
    response = client.post(f'/delete/{meme[id]}', follow_redirects = True)
    assert response.status_code == 200 
    # Ensure the deletion
    assert get_meme_by_name('test.jpg') is None
    assert count_memes() == 0
