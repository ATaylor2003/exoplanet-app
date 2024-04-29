import redis
from flask import Flask, request
import json
import logging
import requests
import os
import csv
from jobs import add_job, get_job_by_id, rd, jdb, res

app = Flask(__name__)

# Configure logging (Prevents any errors in the event if a LOG-LEVEL typo in docker-compose
log_level = os.environ.get('LOG_LEVEL')
if log_level == 'ERROR':
    logging.basicConfig(level=logging.ERROR)
elif log_level == 'WARNING':
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger(__name__)

def convert_none(value):
    """
    Helper Function that converts 'None' values to an empty string. This is to prevent None type errors.

    Args:
    - value: The value to be converted.

    Returns:
    - Converted value. If 'value' is None, returns an empty string.
    """
    return value if value is not None else ''

def convert_redis_data(redis_data):
    """
    Helper function to convert Redis hash data to a dictionary of strings.
    """
    converted_data = {}
    for key, value in redis_data.items():
        converted_data[key.decode()] = value.decode()
    return converted_data

@app.route('/data', methods = ['GET', 'POST', 'DELETE'])
def modify_database():
    """
    Depending on the type of request, make modifications to the redis database. 

    A POST request gets the data from the api in json format and saves each 
    item as a key-value pair in the database. The TIC ids for each planet will represent the key in the pair.

    A DELETE request will delete all key-value pairs of the hgnc data in the redis database.

    A GET request will return all the data currently stored in the redis database.

    returns:
        all_data (list): A list of dictionaries containing the gene data from the HGNC api if the user performs a GET request.
        message (str): A message response if the user performs a POST or DELETE request.
    """

    if request.method == 'POST':
        
        response = requests.get('')
        if response.status_code != 200:
            print("Failed to fetch data from the URL.\n")
            return
        
        data = response.content.decode('utf-8')
        planets = []

        with open('all_data', 'r') as data:
            reader = csv.DictReader(data)
            for row in reader:
                planets.append(dict(row))

            for item in planets:
                rd.set(item['tic_id'], json.dumps(item))

            logging.debug("Number of keys in redis database: " + str(len(rd.keys())) + "\n")

            return "Data saved in redis database!\n" 
    
    if request.method == 'DELETE':
        all_keys = rd.keys()

        for item in all_keys:
            rd.delete(item)
        logging.debug("Number of keys in redis database: " + str(len(rd.keys())) + "\n")

        return "Database cleared!\n"

    if request.method == 'GET':
        all_data = []
        all_keys = rd.keys()

        for item in all_keys:
            all_data.append(json.loads(rd.get(item)))

        return all_data
    
@app.route('/planets', methods = ['GET'])
def return_all_planet_ids():
    """
    This function simply returns all exoplanet TIC ids that were stored as keys in the redis database.

    returns:
        list[str]: a list of all TIC ids in string format
    """
    keys = rd.keys()

    for i in range(len(keys)):
        keys[i] = keys[i].decode('utf-8')

    return keys

@app.route('/planets/<planet_id>', methods = ['GET'])
def return_gene_data(gene_id: str):
    """
    This function returns all the data associated with a given TIC id. If the id doesn't exist, return an empty dictionary

    args:
        gene_id (str): The string representing the id of the planet to search for.

    returns:
        (dict): A dictionary containing the data associated with the given id.
    """
    all_keys = rd.keys()

    for i in range(len(all_keys)):
        all_keys[i] = all_keys[i].decode('utf-8')

    for item in all_keys:
        if item == gene_id:
            return json.loads(rd.get(item))

    logging.error("ID not found. Use the '/planets' route for a list of valid genes stored in the database.\n")
    return {}

@app.route('/jobs', methods = ['GET', 'POST'])
def submit_jobs():
    """
    Depending on the type of request, create a new job or list the jobs that have been created.

    A POST request along with a dictionary containing a 'start_date' and 'end_date' key will create a new job.
    If the dictionary is not passed correctly, return a message. Worker scripts will then create histograms for the jobs.

    A GET request will list all the jobs that have been created

    returns:
        job_dict (dict): The dictionary created when the new job is created
        job_keys (list): A list of job keys that have been created
    """


    if request.method == 'POST':
        data = request.get_json()
        
        job_dict = add_job()
        return job_dict

    if request.method == 'GET':
        job_keys = jdb.keys()
        for i in range(len(job_keys)):
            job_keys[i] = job_keys[i].decode('utf-8')

        return job_keys

@app.route('/jobs/<job_id>', methods = ['GET'])
def get_job_details(job_id: str):
    """
    Return the data associated with a given job, including the processed data if the job is completed. If a job does not exist, return an error message.

    Args:
        job_id (str): The string associated with a job ID that exists

    Returns:
        (dict): A dictionary containing the information for the given job
    """
    
    job_data = get_job_by_id(job_id)

    if type(job_data) is str:
        logging.error("Job not found. Use the '/jobs' route for a list of valid jobs created.\n")
        return {}

    return job_data
    
@app.route('/results/<job_id>', methods = ['GET'])
def get_results(job_id:str):
    """
    Return the resulting plot associated with a given job. If the job does not exist or is still in progress, return a message.

    Args:
        job_id (str): The string associated with a job ID that exists

    Returns:

    """

    job_data = get_job_by_id(job_id)

    if type(job_data) is str:
        logging.error("Job not found. Use the '/jobs' route for a list of valid jobs created.\n")
        return []

    if job_data['status'] != 'completed':
        logging.warning("Job is still in progress. Please wait a moment.")
        return []

    
    with open(path, 'wb') as f:
        f.write(res.hget(jobid, 'image'))

        return send_file(path, mimetype='image/png', as_attachment=True)



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
