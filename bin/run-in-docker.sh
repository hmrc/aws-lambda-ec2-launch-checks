#!/usr/bin/env bash

set -ue

docker run \
  -v "$(pwd)":/src \
  --workdir /src \
  -e POETRY_CACHE_DIR=/src/build/docker/poetry-cache \
  -e POETRY_VIRTUALENVS_PATH=/src/build/docker/virtualenvs \
  -e GITHUB_API_USER="${GITHUB_API_USER:=null}" \
  -e GITHUB_API_TOKEN="${GITHUB_API_TOKEN:=null}" \
  -e MDTP_ENVIRONMENT="${MDTP_ENVIRONMENT:=null}" \
  -e GIT_BRANCH="${GIT_BRANCH:=null}" \
  -e SAM_USE_CONTAINER="${SAM_USE_CONTAINER:=""}" \
  python-build-env \
  "${@}"
