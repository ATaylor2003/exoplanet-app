import redis
from flask import Flask, request, jsonify, send_file
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

def convert_redis_data(redis_data):
    """
    Helper function to convert Redis hash data to a dictionary of strings.
    May be uneccessary for this, can be removed if not used
    """
    converted_data = {}
    for key, value in redis_data.items():
        converted_data[key.decode()] = value.decode()
    return converted_data

# Define a dictionary mapping routes to their descriptions and additional details
route_details = {
    "/data": {
        "description": "Modify the Redis database based on request type.",
        "methods": ["POST", "DELETE", "GET"],
        "usage": {
            "POST": {
                "description": "Add data to the Redis database.",
                "parameters": {
                    "data": "The data to be added."
                },
                "example": "/data (POST)"
            },
            "DELETE": {
                "description": "Clear all data in the Redis database.",
                "parameters": {},
                "example": "/data (DELETE)"
            },
            "GET": {
                "description": "Retrieve all data from the Redis database.",
                "parameters": {},
                "example": "/data (GET)"
            }
        }
    },
    "/planets": {
        "description": "Retrieve a list of all exoplanet IDs stored in the Redis database.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Retrieve a list of exoplanet IDs.",
                "parameters": {},
                "example": "/planets"
            }
        }
    },
    "/planets/<planet_id>": {
        "description": "Retrieve data associated with a specific exoplanet ID.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Retrieve data for a specific exoplanet ID.",
                "parameters": {
                    "planet_id": "The ID of the exoplanet."
                },
                "example": "/planets/12345"
            }
        }
    }, 
    "/planets/filter": {
        "description": "Retrieve and filter data based on criteria.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Filter data based on criteria.",
                "parameters": {
                    "key=value": "The key in the data to filter by and a value to search for"
                },
                "example": "planets/filter?disc_facility=Xinglong%20Station"
            }
        }
    },
    "/planets/search": {
        "description": "Search and retrieve data for exoplanets based on the name given in the search.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Search and retrieve data for specific exoplanets.",
                "parameters": {
                    "name=planet_name": "The name of the planet to search for (case insensitive)"
                },
                "example": "planets/search?name=kepler-1066%20b"
            }
        }
    }, 
    "/planets/advanced-filter": {
        "description": "Retrieve and filter data based on multiple criteria.",
        "methods": ["POST"],
        "usage": {
            "POST": {
                "description": "Filter data based on multiple criteria.",
                "parameters": {
                    "{'filters': {'key1': 'value',...}": "A json dictionary containing the keys to filter by and the values to search for"
                },
                "example": "planets/advanced-filter' -d '{'filters': {'discoverymethod': 'Transit'}}' -H 'Content-Type: application/json'"
            }
        }
    }, 
    "/stars": {
        "description": "Retrieve a list of all stars associated with exoplanets.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Retrieve a list of star names.",
                "parameters": {},
                "example": "/stars"
            }
        }
    },
    "/stars/<star_id>": {
        "description": "Retrieve a list of exoplanets associated with a specific star.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Retrieve a list of planets for a specific star.",
                "parameters": {
                    "star_id": "The name of the star."
                },
                "example": "/stars/Star1"
            }
        }
    },
    "/jobs": {
        "description": "Submit new jobs for data plotting or retrieve a list of all created jobs. 'organize_by' is optional and options are 'Mass', 'Radius', and 'Orbit_Period'. Otherwise organize by year.",
        "methods": ["POST", "GET"],
        "usage": {
            "POST": {
                "description": "Submit a new job for data plotting.",
                "parameters": {
                    "data": "The json dictionary that determines the data to plot."
                },
                "example": "/jobs' -d '{'start_date': 2000, 'end_date': 2009, 'organize_by': 'Orbit_Period'}' -H 'Content-Type: application/json'"
            },
            "GET": {
                "description": "Retrieve a list of all created jobs.",
                "parameters": {},
                "example": "/jobs (GET)"
            }
        }
    },
    "/jobs/<job_id>": {
        "description": "Retrieve details about a specific job based on its ID.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Retrieve details for a specific job.",
                "parameters": {
                    "job_id": "The ID of the job."
                },
                "example": "/jobs/54321"
            }
        }
    },
    "/results/<job_id>": {
        "description": "Retrieve and download the resulting plot associated with a specific job ID.",
        "methods": ["GET"],
        "usage": {
            "GET": {
                "description": "Retrieve the plot result for a specific job.",
                "parameters": {
                    "job_id": "The ID of the job."
                },
                "example": "/results/54321"
            }
        }
    }
}

@app.route('/help', methods=['GET'])
def help():
    """
    Return descriptions and usage details of all available routes.

    Returns:
        dict: A dictionary containing route descriptions and usage details.
    """
    return jsonify(route_details), 200

@app.route('/data', methods = ['GET', 'POST', 'DELETE'])
def modify_database():
    """
    Depending on the type of request, make modifications to the redis database. 

    A POST request gets the data from the api in json format and saves each 
    item as a key-value pair in the database. The TIC ids for each planet will represent the key in the pair.

    A DELETE request will delete all key-value pairs of the hgnc data in the redis database.

    A GET request will return all the data currently stored in the redis database.

    The below url contains table data:
    https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html#addtldata

    returns:
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
                planet_id = item.get('pl_name')  # Assuming 'pl_name' is the identifier; adjust if necessary
                if planet_id:
                    rd.set(planet_id, json.dumps(item))
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
        """
        Retrieve data from the Redis database based on query parameters.

        Query Parameters:
            - limit (int, optional): Limit the number of records returned.
            - planet_name (str, optional): Filter records by planet name.

        Returns:
            list: A list of data records matching the query criteria.
        """
        limit = request.args.get('limit', default=None, type=int)
        planet_name = request.args.get('planet_name', default=None, type=str)

        all_data = [json.loads(rd.get(key)) for key in rd.keys('*')]

        if planet_name:
            filtered_data = [record for record in all_data if record.get('pl_name') == planet_name]
        else:
            filtered_data = all_data

        if limit:
            filtered_data = filtered_data[:limit]

        return jsonify(filtered_data), 200
    
@app.route('/planets', methods = ['GET'])
def return_all_planet_ids():
    """
    This function returns all exoplanet IDs that were stored as keys in the redis database.

    returns:
        list[str]: a list of all explanet IDs in string format
    """
    keys = rd.keys()

    for i in range(len(keys)):
        keys[i] = keys[i].decode('utf-8')

    return keys

# Endpoint to filter based on one of the keys of the datase, for example Discovery Facility -> Xinglong Station: curl -X GET "http://localhost:5000/planets/filter?disc_facility=Xinglong%20Station"
@app.route('/planets/filter', methods=['GET'])
def filter_planets():
    query_parameters = request.args

    # Retrieve all exoplanet data from Redis (assuming 'rd' is your Redis connection)
    keys = rd.keys()
    exoplanets = [json.loads(rd.get(key)) for key in keys]

    filtered_planets = exoplanets
    for key, value in query_parameters.items():
        filtered_planets = [planet for planet in filtered_planets if str(planet.get(key)) == value]

    return jsonify(filtered_planets)

# Endpoint to search exoplanets by name, for example name -> Kepler-1066 b: curl -X GET "127.0.0.1:5000/planets/search?name=Kepler-1066%20b"
@app.route('/planets/search', methods=['GET'])
def search_planets():
    name = request.args.get('name')
    if not name:
        return jsonify({'message': 'Search term "name" is required'}), 400

    try:
        # Retrieve all exoplanet data from Redis (assuming 'rd' is your Redis connection)
        keys = rd.keys()
        exoplanets = [json.loads(rd.get(key)) for key in keys]

        # Filter exoplanets by name (case-insensitive)
        filtered_planets = [planet for planet in exoplanets if planet.get('pl_name', '').lower() == name.lower()]

        return jsonify(filtered_planets), 200
    except Exception as e:
        logging.error(f"An error occurred while searching for exoplanets: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500


@app.route('/stars', methods=['GET'])
def list_unique_stars():
    """
    Return a list of all unique star 'hostname' values stored in the Redis database.

    Returns:
        json: A JSON object containing a list of unique 'hostname' values, or an error message.
    """
    try:
        all_keys = rd.keys()  # Retrieve all keys from Redis
        hostnames = set()  # A set to store unique hostnames
        
        for key in all_keys:
            star_data = json.loads(rd.get(key).decode('utf-8'))  # Decode and load data for each key
            hostname = star_data.get('hostname')
            if hostname:
                hostnames.add(hostname)  # Add the hostname to the set if it's not None

        return jsonify({'List of stars present in database': list(hostnames)}), 200  # Return the list of unique hostnames

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

# Endpoint to retrieve exoplanets orbiting a specific star by ID
@app.route('/stars/<star_id>', methods=['GET'])
def get_star(star_id: str):
    """
    Retrieve all keys where the 'hostname' in their associated data matches the given star_id.

    Args:
        star_id (str): The hostname ID of the star to search for in Redis.

    Returns:
        json: A list of exoplanet keys that have data with the specified 'hostname', or an error message.
    """
    try:
        all_keys = rd.keys()  # Retrieve all keys from Redis
        matching_keys = []  # List to store keys that match the 'hostname'
        
        for key in all_keys:
            star_data = json.loads(rd.get(key).decode('utf-8'))  # Decode and load data for each key
            if star_data.get('hostname') == star_id:  # Check if the 'hostname' matches the star_id
                matching_keys.append(key.decode('utf-8'))  # Add the key to the list if it matches

        if matching_keys:
            return jsonify({('Exoplanets orbiting ' + star_id): matching_keys}), 200  # Return the list of matching keys
        else:
            # If no matching 'hostname' is found after checking all keys
            logging.error("Star ID not found. Use the '/planets' route for a list of valid exoplanets stored in the database.")
            return jsonify({'message': 'Star not found'}), 404

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

# Endpoint to filter based on more than one of the keys of the datase, for example hostname -> TOI-332 & Discovery Method -> Transit
# curl -X POST \
#  -H "Content-Type: application/json" \
#  -d '{
#        "filters": {
#          "hostname": "TOI-332",
#          "discoverymethod": "Transit"
#        }
#      }' \
#  http://127.0.0.1:5000/planets/advanced-filter

@app.route('/planets/advanced-filter', methods=['POST'])
def advanced_filter_planets():
    try:
        filters = request.get_json()
        if not filters or 'filters' not in filters:
            return jsonify({'message': 'Invalid request body'}), 400
        
        filters = filters['filters']
        
        # Retrieve exoplanets data from Redis or another source
        keys = rd.keys()
        exoplanets = [json.loads(rd.get(key)) for key in keys]

        # Apply filters to the exoplanets data
        filtered_planets = exoplanets
        for key, value in filters.items():
            filtered_planets = [planet for planet in filtered_planets if str(planet.get(key)) == str(value)]

        return jsonify(filtered_planets), 200

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500


#Currently spaces must be interpreted as %20 ie K2-374%20c
@app.route('/planets/<planet_id>', methods = ['GET'])
def return_planet_data(planet_id: str):
    """
    This function returns all the data associated with a given planet name id. If the name doesn't exist, return an empty dictionary

    args:
        planet_id (str): The string representing the id of the planet to search for.

    returns:
        (dict): A dictionary containing the data associated with the given id.
    """
    all_keys = rd.keys()

    for i in range(len(all_keys)):
        all_keys[i] = all_keys[i].decode('utf-8')

    for item in all_keys:
        if item == planet_id:
            return json.loads(rd.get(item))

    logging.error("ID not found. Use the '/planets' route for a list of valid exoplanets stored in the database.\n")
    return {}


@app.route('/jobs', methods = ['GET', 'POST'])
def submit_jobs():
    """
    Depending on the type of request, create a new job or list the jobs that have been created.

    A POST request along with a dictionary containing a 'start_date', 'end_date', and an optional 'organize_by' key will create a new job.
    If the dictionary is not passed correctly, return a message. Worker scripts will then create histograms for the jobs.

    A GET request will list all the jobs that have been created

    returns:
        job_dict (dict): The dictionary created when the new job is created
        job_keys (list): A list of job keys that have been created
    """


    if request.method == 'POST':
        data = request.get_json()
        valid_plot_options = ['Mass', 'Radius', 'Orbit_Period']

        try:
            limit = int(data['start_date'])
        except KeyError or ValueError:
            logging.error("Error creating job: a 'start_date' parameter must exist and it must be an integer.\n")
            return {}
        try:
            offset = int(data['end_date'])
        except KeyError or ValueError:
            logging.error("Error creating job: an 'end_date' parameter must exist and it must be an integer.\n")
            return {}

        try:
            if data['organize_by'] in valid_plot_options:
                job_dict = add_job(data['start_date'], data['end_date'], data['organize_by'])
            else:
                logging.error("Error creating job: Valid organizations are 'Radius', 'Mass', and 'Orbit_Period'\n")
                return{}
        except KeyError:
            # If the route is passed with only years, organize by years
            job_dict = add_job(data['start_date'], data['end_date'])

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

    path = f'/app/{job_id}.png'

    if type(job_data) is str:
        logging.error("Job not found. Use the '/jobs' route for a list of valid jobs created.\n")
        return []

    if job_data['status'] != 'completed':
        logging.warning("Job is still in progress. Please wait a moment.")
        return []

    
    with open(path, 'wb') as f:
        f.write(res.hget(job_id, 'image'))

        return send_file(path, mimetype='image/png', as_attachment=True)



if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
