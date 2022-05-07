#!/bin/bash

SCRIPT_PATH=$(readlink -f `dirname "$0"`)
cd ${SCRIPT_PATH}

exec celery "$@"
