#!/bin/bash

### WARNING! This is a generated file and should ONLY be edited in https://github.com/hmrc/telemetry-lambda-resources

set -eu

apt install -y libssl-dev zip
mkdir -p build
# Package the dependencies
cd "./${VENV_NAME}/lib/python3.9/site-packages"
zip -r "../../../../build/${LAMBDA_ZIP_NAME}" .
cd -
# Package the source
cd "./src"
zip -r --grow "../build/${LAMBDA_ZIP_NAME}" .
# Generate the hash file
openssl dgst -sha256 -binary "../build/${LAMBDA_ZIP_NAME}" | openssl enc -base64 >"../build/${LAMBDA_HASH_NAME}"
cd -
