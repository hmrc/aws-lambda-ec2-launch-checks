#!/usr/bin/env bash

set -eu

# Initialise directories
BASEDIR=/data
cd ${BASEDIR}

# Force Debian to use HTTPS
cp /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list.d/debian.sources.bak
sed --in-place 's|http://|https://|g' /etc/apt/sources.list.d/debian.sources

# Update the package listing, so we know what package exist:
apt-get update && apt-get -y upgrade && apt-get install -y libssl-dev zip

# Install requirements
python -m venv "${VENV_NAME}"
source "${VENV_NAME}/bin/activate"

# The platform argument ensures greater compatibility with AWS Lambda Runtimes
# https://repost.aws/knowledge-center/lambda-python-package-compatible
# https://github.com/pypa/manylinux - The chosen platform will be EOL June 2024

# force reinstall cryptography to ensure it uses rust utils
pip install --index-url "${PIP_INDEX_URL}" --force-reinstall cryptography

pip install --requirement "${REQUIREMENTS_FILE}" \
            --implementation cp \
            --index-url "${PIP_INDEX_URL}" \
            --only-binary=:all: \
            --platform "manylinux_2_28_x86_64" \
            --platform "manylinux2014_x86_64" \
            --target="./${VENV_NAME}/lib/python${PYTHON_VERSION_LIB}/site-packages"

# Make the binary location specified in --target above, available to PATH
export PATH="$PATH:./${VENV_NAME}/lib/python${PYTHON_VERSION_LIB}/site-packages/bin"

exec "$@"
