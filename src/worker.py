from jobs import get_job_by_id, update_job_status, q, rd, res
import json
import logging
import matplotlib.pyplot as plt

@q.worker
def update_job():
    """
    Watch for new jobs and process them accordingly.
    """
    while True:
        job_id = q.dequeue()
        if job_id:
            process_job(job_id)
        else:
            break

def process_job(job_id: str):
    """
    Process a specific job by generating a plot and storing the resulting image.
    
    Args:
        job_id (str): The ID of the job to process.
    """
    update_job_status(job_id, 'in_progress')
    job_dict = get_job_by_id(job_id)

    # Example: Generate a plot based on job instructions
    plot_type = job_dict.get('plot_type', 'default')
    if plot_type == 'scatter':
        data = job_dict.get('data', [])
        x_values = [entry['x'] for entry in data]
        y_values = [entry['y'] for entry in data]
        plt.scatter(x_values, y_values)
        plt.xlabel('X-axis')
        plt.ylabel('Y-axis')
        plt.title('Scatter Plot')
        plt.grid(True)
        plt.savefig(f'{job_id}_plot.png')
        plt.close()

        # Store resulting image in Redis database
        with open(f'{job_id}_plot.png', 'rb') as image_file:
            image_data = image_file.read()
            rd.set(job_id, image_data)

        update_job_status(job_id, 'completed')
        logging.info(f"Job {job_id} completed successfully.")
    else:
        update_job_status(job_id, 'failed')
        logging.error(f"Unsupported plot type '{plot_type}' for job {job_id}.")

if __name__ == '__main__':
    update_job()
