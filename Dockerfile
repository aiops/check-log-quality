 # docker build -t log-anomaly-detection .

# set base image (host OS)
FROM python:3.8-slim

# set the working directory in the container
WORKDIR /work

COPY python/requirements.txt .
# install dependencies
RUN pip install -r requirements.txt
COPY . .

ENTRYPOINT [ "./check-log-quality" ]
