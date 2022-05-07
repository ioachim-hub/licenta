#!/bin/bashd

SCRIPT_PATH=$(readlink -f `dirname "$0"`)
cd ${SCRIPT_PATH}/predicter

python3 manage.py runserver 0.0.0.0:8080
