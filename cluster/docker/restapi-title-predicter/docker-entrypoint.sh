#!/bin/bash

SCRIPT_PATH=$(readlink -f `dirname "$0"`)
cd ${SCRIPT_PATH}

python3 -m fakepred.restapi_title_predicter.main
