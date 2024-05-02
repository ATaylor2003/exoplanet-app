FROM python:3.10

RUN mkdir /app
WORKDIR /app

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY src/flask_api.py src/worker.py src/jobs.py ./
COPY test/test_api.py test/test_worker.py test/test_jobs.py ./

ENV REDIS_IP="redis-db"
ENV REDIS_PORT="6379"
ENV LOG_LEGEL="WARNING"

CMD ["python3"]


