#!/bin/bash

SCRIPT_PATH=$(readlink -f `dirname "$0"`)
ROOT_PATH=${SCRIPT_PATH}/..

CONFIG_PATH=${SCRIPT_PATH}/mgr_cfg.json

source ${ROOT_PATH}/../licenta-env/bin/activate
${ROOT_PATH}/charts/mgr.py --config ${CONFIG_PATH} --root_path ${ROOT_PATH} $@
