FROM docker.io/python:3.10.2-bullseye

USER root

COPY ./licenta_code /opt/licenta_code
RUN chmod 777 /opt/licenta_code

COPY requirements-celery-similarity.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./docker/celery-similarity/docker-entrypoint.sh /opt/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1

RUN chmod 777 /root/

ENTRYPOINT ["/opt/docker-entrypoint.sh"]
