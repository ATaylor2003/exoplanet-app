import pytest
import requests
import time

post_response = requests.post('http://127.0.0.1:5000/data')

dictionary = {'start_date': '2000', 'end_date': '2001'}
job_response = requests.post('http://127.0.0.1:5000/jobs', json=dictionary)
job_id = job_response.json()['id']
time.sleep(10)
job_id_response = requests.get('http://127.0.0.1:5000/jobs/' + job_id)
results_response = requests.get('http://127.0.0.1:5000/results/' + job_id)

invalid_job_id_response = requests.get('http://127.0.0.1:5000/jobs/0')
invalid_results_response = requests.get('http://127.0.0.1:5000/results/0')

delete_response = requests.delete('http://127.0.0.1:5000/data')

def test_jobs_and_worker():
    assert job_response.status_code == 200
    assert isinstance(job_response.json(), dict) == True

    assert job_id_response.status_code == 200
    assert isinstance(job_id_response.json(), dict) == True

    assert results_response.status_code == 200
    assert b'PNG' in results_response.content

    assert invalid_job_id_response.status_code == 200
    assert invalid_job_id_response.json() == {}

    assert invalid_results_response.status_code == 200
    assert invalid_results_response.json() == []

