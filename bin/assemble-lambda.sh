#!/bin/bash

set -eu

apt install -y zip
mkdir -p build
cd "./${VENV_NAME}/lib/python3.8/site-packages"
zip -r "../../../../build/${LAMBDA_ZIP_NAME}" .
cd -
zip --grow --junk-paths "./build/${LAMBDA_ZIP_NAME}" ./src/handler.py
