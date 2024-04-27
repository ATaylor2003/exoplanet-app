from jobs import get_job_by_id, update_job_status, q, rd, res
import json
import logging
import matplotlib.pyplot as plt

@q.worker
def update_job(job_id: str):
    """

        Args:
            job_id (str): The string associated with a given job ID

        Returns:
            
    """
    update_job_status(job_id, 'in_progress')
    job_dict = get_job_by_id(job_id)

    res.set(job_id, json.dumps(result_plot))

    update_job_status(job_id, 'completed')

    return ''


update_job()
