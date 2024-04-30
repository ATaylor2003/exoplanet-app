import json
import uuid
import redis
import os
from hotqueue import HotQueue

_redis_ip = os.environ["REDIS_IP"]
_redis_port = os.environ["REDIS_PORT"]

rd = redis.Redis(host=_redis_ip, port=_redis_port, db=0)
q = HotQueue("queue", host=_redis_ip, port=_redis_port, db=1)
jdb = redis.Redis(host=_redis_ip, port=_redis_port, db=2)
res = redis.Redis(host=_redis_ip, port=_redis_port, db=3)

def _generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """
    return str(uuid.uuid4())

def _instantiate_job(jid: str, status: str, start_date: int, end_date: int, organize_by: str):
    """
    Create the job object description as a python dictionary. Requires the job id,
    status, limit and offset parameters.
    """
    return {'id': jid,
            'status': status,
            'start_date': start_date,
            'end_date': end_date,
            'organize_by': organize_by}

def _save_job(jid: str, job_dict: dict):
    """Save a job object in the Redis database."""
    jdb.set(jid, json.dumps(job_dict))
    return

def _queue_job(jid: str):
    """Add a job to the redis queue."""
    q.put(jid)
    return

def add_job(start_date: int, end_date: int, organize_by="None", status="submitted"):
    """Add a job to the redis queue."""
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, start_date, end_date, organize_by)
    _save_job(jid, job_dict)
    _queue_job(jid)
    return job_dict

def get_job_by_id(jid: str):
    """Return job dictionary given jid"""
    if jdb.get(jid) is None:
        return "Job not found\n"
    return json.loads(jdb.get(jid))

def update_job_status(jid: str, status: str):
    """Update the status of job with job id `jid` to status `status`."""
    job_dict = get_job_by_id(jid)
    if job_dict:
        job_dict['status'] = status
        _save_job(jid, job_dict)
    else:
        raise Exception()
