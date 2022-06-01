FROM docker.io/bitnami/python:3.9.8-debian-10-r1

USER root

COPY ./fakepred /opt/fakepred
RUN chmod 777 /opt/fakepred

#Upgrade pip
RUN pip3 install --no-cache-dir -U pip
#The upgrade setuptools
RUN rm -r /opt/bitnami/python/lib/python3.9/site-packages/setuptools*
RUN pip3 install --no-cache-dir -U setuptools

COPY requirements-celery-beat.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./docker/celery-beat/docker-entrypoint.sh /opt/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1


ENTRYPOINT ["/opt/docker-entrypoint.sh"]
