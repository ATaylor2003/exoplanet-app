import redis
from flask import Flask, request, jsonify
import json
import logging
import requests
import os
import csv
import urllib.parse
from jobs import add_job, get_job_by_id, rd, jdb, res

app = Flask(__name__)

# Configure logging (Prevents any errors in the event of a LOG-LEVEL typo in docker-compose
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
        base_url = 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync'
        query = 'select * from ps'
        encoded_query = urllib.parse.quote_plus(query)
        url = f"{base_url}?query={encoded_query}&format=json"
        response = requests.get(url)
        print("URL Requested:", url)
        if response.status_code != 200:
            print("Failed to fetch data from the URL.\n")
            return "Failed to fetch data", 502
        
        data = response.json()
        #print("Stuff is happening!")
        if isinstance(data, list):  # Expecting a list of dictionaries
            for item in data:
                tic_id = item.get('pl_name')  # Assuming 'pl_name' is the identifier; adjust if necessary
                if tic_id:
                    rd.set(tic_id, json.dumps(item))
            return f"{len(data)} records saved in Redis.", 200
        else:
            return "Invalid JSON format: List of dictionaries expected", 400
        
    
    elif request.method == 'DELETE':
        keys_deleted = 0
        for key in rd.keys('*'):
            rd.delete(key)
            keys_deleted += 1
        
        return f"Deleted {keys_deleted} records from Redis.", 200
    
    elif request.method == 'GET':
        all_data = [json.loads(rd.get(key)) for key in rd.keys('*')]
        return jsonify(all_data), 200
    
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
