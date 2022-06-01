FROM docker.io/python:3.10.2-bullseye

USER root

COPY ./fakepred /opt/fakepred
RUN chmod 777 /opt/fakepred

RUN mkdir -p /opt/trained_models
COPY ./trained_models/pytorch_fakerobertmodel_content_cpu.bin /opt/trained_models/pytorch_fakerobertmodel_content_cpu.bin

COPY requirements-restapi-predicter.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./docker/restapi-content-predicter/docker-entrypoint.sh /opt/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1 PYTHONOPTIMIZE=0 PYTHONDONTWRITEBYTECODE=1

RUN chmod 777 /root/

ENTRYPOINT ["/opt/docker-entrypoint.sh"]
