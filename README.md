# NASA Exoplanet Archive Database Application

The Exoplanet Archive Database Application provides an app for retireving, parsing, and graphing data from the NASA Exoplanet Archive [1]. The primary script, flask_api.py, fetches the exoplanet data from the archive and adds it to a redis database, from which the entire dataset can be retrieved in json format or information regarding specific planets can be retrieved. Additionally, filters can be applied in order to produce a more narrow dataset and stars can be searched in order to find their respective exoplanetary satellites.

## Folder Contents

- **src** - source file folder
  - **flask_api.py**: Python3 app script for fetching exoplanet data and adding it to a redis database, as well as retrieving information.
  - **jobs.py**: Module containing several helper functions for creating, identifying, and updating jobs.
  - **worker.py**: Script that uses hotqueue to accept jobs and create graphs based on inputs.
- **test** - test file folder
  - **test_api.py**: Script for testing gene api scripts.
  - **test_jobs.py**: Scipt for testing the job functions (calls major functions that accesses the rest of the functions).
  - **test_worker.py**: Script for testing the worker functions.
- **Dockerfile**: Dockerfile for building the Docker image containing the app scripts and uses dependencies from requirements.txt.
- **requirements.txt**: contains code dependencies
- **docker-compose.yaml**: Composition file for creating the flask and redis server images.
- **data** - output log data folder
- **kubernetes** - kubernetes folder
   - **prod** - product folder containing the necessary files for deploying the app via kubernetes
      - app-prod-deployment-flask.yml
      - app-prod-deployment-redis.yml
      - app-prod-deployment-worker.yml
      - app-prod-ingress-flask.yml
      - app-prod-pvc-redis.yml
      - app-prod-service-flask.yml
      - app-prod-service-nodeport-flask-yml
      - app-prod-service-redis.yml
    - **test** - test folder for the creation of a test environment
      - app-test-deployment-flask.yml
      - app-test-deployment-redis.yml
      - app-test-deployment-worker.yml
      - app-test-ingress-flask.yml
      - app-test-pvc-redis.yml
      - app-test-service-flask.yml
      - app-test-service-nodeport-flask-yml
      - app-test-service-redis.yml



### The Data Used

The data used in the application can be obtained from the [Planetary Systems Spreadsheet in the NASA Exoplanet Science Institute](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=PS). The data is downloaded in csv format.

### Deploying and Testing the Application Locally

### Deploying and Testing using Kubernetes

### Using the Application

### Using the Application with Public Endpoints

### Software Diagram
