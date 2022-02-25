FROM docker.io/bitnami/python:3.9.8-debian-10-r1

USER root

COPY ./licenta_code/predicter /opt/predicter
RUN chmod 777 /opt/predicter

COPY requirements-django.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./docker/predicter/docker-entrypoint.sh /opt/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/predicter
EXPOSE 80

CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]
