import json
import pytest

# Add the parent directory to sys.path if needed
import sys
sys.path.append('../src')

from flask_api import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_help_route(client):
    """Test the help route to ensure it returns the expected status code and data structure."""
    response = client.get('/help')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert type(data) == dict
    assert "/data" in data

def test_post_data(client):
    """Test POST to /data route to simulate adding data to the Redis database."""
    response = client.post('/data', json={"data": "test_data"})
    assert response.status_code == 200

def test_delete_data(client):
    """Test DELETE to /data route to clear the Redis database."""
    response = client.delete('/data')
    assert response.status_code == 200

def test_get_data(client):
    """Test GET to /data route to retrieve data from Redis database."""
    response = client.get('/data')
    assert response.status_code == 200

def test_search_planets(client):
    """Test searching planets by name."""
    response = client.get('/planets/search?name=Kepler-10b')
    assert response.status_code == 200

def test_list_unique_stars(client):
    """Test listing unique stars."""
    response = client.get('/stars')
    assert response.status_code == 200

def test_create_job(client):
    """Test job submission."""
    job_data = {
        "start_date": "2010",
        "end_date": "2020",
        "organize_by": "Mass"
    }
    response = client.post('/jobs', json=job_data)
    assert response.status_code == 200

def test_get_job_details(client):
    """Test retrieving job details."""
    response = client.get('/jobs/1')  # assuming a job with ID '1' exists
    assert response.status_code == 200
