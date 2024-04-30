from jobs import get_job_by_id, update_job_status, q, rd, res
import json
import logging
import matplotlib.pyplot as plt

### Needs fixing
@q.worker
def update_job(job): # Gave an error if this argument wasn't there
    """
    Watch for new jobs and process them accordingly.
    """
    while True:
        job_id = q.dequeue() # Says HotQueue has no attribute dequeue
        if job_id:
            process_job(job_id)
        else:
            break

def process_job(job_id: str):
    """
    Process a specific job by generating a histogram and storing the resulting image.
    
    Args:
        job_id (str): The ID of the job to process.
    """
    update_job_status(job_id, 'in_progress')
    job_dict = get_job_by_id(job_id)

    # Example: Generate a plot based on job instructions
    # plot_type = job_dict.get('plot_type', 'default')
    values_to_plot = []
    all_keys = rd.keys()

    if job_dict['organize_by'] == 'None':
        x_axis = 'disc_year'
        x_title = 'year_discovered'
    elif job_dict['organize_by'] == 'Mass':
        x_axis = 'pl_masse'
        x_title = 'Mass of planet (Earth Masses)'
    elif job_dict['organize_by'] == 'Radius':
        x_axis = 'pl_rade'
        x_title = 'Radius of planet (Earth Radii)'
    elif job_dict['organize_by'] == 'Orbit_Period':
        x_axis = 'pl_orbper'
        x_title = 'Orbit Period (Earth Days)'
    else:
        update_job_status(job_id, 'failed')
        logging.error(f"Unsupported plot type '{plot_type}' for job {job_id}.")
        return ''

    for key in all_keys:
        planet = json.loads(rd.get(key))
        try:
            values_to_plot.append(float(planet([x_axis])))
        except ValueError:
            continue

    plt.hist(values_to_plot, 20)
    plt.xlabel(x_title)
    plt.y_label('Frequency')
    plt.title('Histogram')
    plt.savefig(f'{job_id}_plot.png')
    plt.close

    # Store resulting image in Redis database
    with open(f'{job_id}_plot.png', 'rb') as image_file:
        image_data = image_file.read()
        res.hset(job_id, 'image', image_data)

    update_job_status(job_id, 'completed')
    logging.info(f"Job {job_id} completed successfully.")

if __name__ == '__main__':
    update_job()
