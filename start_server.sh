#!/bin/bash

cd "$(dirname "$0")"

. ./venv/bin/activate
./venv/bin/python ./main.py >> modbus_server.log
