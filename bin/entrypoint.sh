#!/bin/bash

### WARNING! This is a generated file and should ONLY be edited in https://github.com/hmrc/telemetry-lambda-resources

set -xeu

# Debug Python environment
python --version
pip --version

# Initialise directories
BASEDIR=/data
cd ${BASEDIR}

# Force Debian to use HTTPS
cp /etc/apt/sources.list /etc/apt/sources.list.bak
sed --in-place 's|http://|https://|g' /etc/apt/sources.list

# Update the package listing, so we know what package exist:
apt-get update

# Install security updates:
apt-get -y upgrade

# Install test requirements
python -m venv "${VENV_NAME}"
source ./"${VENV_NAME}"/bin/activate

# The platform argument ensures greater compatibility with AWS Lambda Runtimes
# https://repost.aws/knowledge-center/lambda-python-package-compatible
# https://github.com/pypa/manylinux - The chosen platform will be EOL June 2024
pip install --index-url https://artefacts.tax.service.gov.uk/artifactory/api/pypi/pips/simple --upgrade pip
pip install --index-url https://artefacts.tax.service.gov.uk/artifactory/api/pypi/pips/simple \
            --requirement "${REQUIREMENTS_FILE}" \
            --platform manylinux2014_x86_64 \
            --target=./${VENV_NAME}/lib/python3.9/site-packages \
            --implementation cp \
            --only-binary=:all:

# Make the binary location specified in --target above, available to PATH
export PATH="$PATH:./${VENV_NAME}/lib/python3.9/site-packages/bin"

exec "$@"
