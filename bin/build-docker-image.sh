#! /usr/bin/env bash

set -ue

MY_DIR="$(dirname "${BASH_SOURCE[0]}")"

PYTHON_VERSION="$(head -1 "${MY_DIR}/../.python-version")"
POETRY_VERSION="$(head -1 "${MY_DIR}/../.poetry-version")"

docker build \
  --build-arg PYTHON_VERSION="${PYTHON_VERSION}" \
  --build-arg POETRY_VERSION="${POETRY_VERSION}" \
  --build-arg APP_USER_ID="$(id -u)" \
  --build-arg APP_GROUP_ID="$(id -g)" \
  -t python-build-env \
  -f Dockerfile .
