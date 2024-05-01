from jobs import get_job_by_id, update_job_status, q, rd, res
import json
import logging
import matplotlib.pyplot as plt

@q.worker
def process_job(job_id: str):
    """
    Process a specific job by generating a histogram and storing the resulting image.
    
    Args:
        job_id (str): The ID of the job to process.
    """
    update_job_status(job_id, 'in_progress')
    job_dict = get_job_by_id(job_id)

    values_to_plot = []
    all_keys = rd.keys()

    start_date = int(job_dict['start_date'])
    end_date = int(job_dict['end_date'])

    if job_dict['organize_by'] == 'None':
        x_axis = 'disc_year'
        x_title = 'Year Discovered'
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
        logging.error(f"Unsupported plot organization for job {job_id}.")
        return ''

    for key in all_keys:
        planet = json.loads(rd.get(key))
        try:
            if ((int(planet['disc_year'])) >= start_date) and (int(planet['disc_year']) <= end_date):
                values_to_plot.append(int(planet[x_axis]))
        except TypeError:
            continue

    num_bins = 20
    if x_axis == 'disc_year':
        num_bins = max((end_date - start_date), 1)
    
    plt.hist(values_to_plot, num_bins)
    plt.xlabel(x_title)
    plt.ylabel('Number of Exoplanets')
    plt.title(f'Summary of Planets Discovered Between {start_date} and {end_date}')
    plt.savefig(f'{job_id}_plot.png')
    plt.close

    # Store resulting image in Redis database
    with open(f'{job_id}_plot.png', 'rb') as image_file:
        image_data = image_file.read()
        res.hset(job_id, 'image', image_data)

    update_job_status(job_id, 'completed')
    logging.info(f"Job {job_id} completed successfully.")

if __name__ == '__main__':
    process_job()
