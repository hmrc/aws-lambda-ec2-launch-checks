#!/usr/bin/env bash

set -eu

mkdir -p build
cd "./${VENV_NAME}/lib/python${PYTHON_VERSION_LIB}/site-packages"
zip -r "../../../../build/package.zip" .
cd -
cd "./src"
zip -r --grow "../build/package.zip" .
cd -
