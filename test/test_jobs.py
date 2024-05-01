import pytest
import time
from jobs import add_job
from jobs import get_job_by_id
from jobs import update_job_status

def test_add_job():
    assert isinstance(add_job(0, 0), dict) == True
    assert isinstance(add_job(0, 0, "Radius"), dict) == True

def test_get_job_by_id():
    test_dict = add_job(2000, 2020)
    test_id = test_dict['id']
    assert get_job_by_id(test_id) == test_dict

    time.sleep(10)
    
    test_dict['status'] = 'completed'
    assert get_job_by_id(test_id) == test_dict
    

    assert get_job_by_id('test') == "Job not found\n"

def test_update_job_status():
    test_dict = add_job(0, 0)
    test_dict['status'] = 'testing'
    test_id = test_dict['id']

    update_job_status(test_id, 'testing')
    assert get_job_by_id(test_id) == test_dict


    with pytest.raises(Exception):
        update_job_status('test', 'testing')
