#!/bin/bash

set -eu

apt install -y zip
mkdir -p build
cd "./${VENV_NAME}/lib/python3.9/site-packages"
zip -r "../../../../build/${LAMBDA_ZIP_NAME}" .
cd -
cd "./src"
zip -r --grow "../build/${LAMBDA_ZIP_NAME}" .
cd -
