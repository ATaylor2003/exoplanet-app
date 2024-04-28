FROM python:3.10

RUN mkdir /app
WORKDIR /app

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY src/api.py src/worker.py src/jobs.py ./
COPY test/test_api.py test/test_worker.py test/test_jobs.py ./

CMD ["python3"]


