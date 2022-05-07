FROM docker.io/python:3.10.2-bullseye

USER root

COPY ./licenta_code /opt/licenta_code
RUN chmod 777 /opt/licenta_code

#Upgrade pip
RUN pip3 install --no-cache-dir -U pip

RUN pip3 install --no-cache-dir -U setuptools

COPY requirements-celery-completer.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./docker/celery-completer/docker-entrypoint.sh /opt/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["/opt/docker-entrypoint.sh"]
