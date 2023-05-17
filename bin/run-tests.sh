#!/bin/bash

### WARNING! This is a generated file and should ONLY be edited in https://github.com/hmrc/telemetry-lambda-resources

set -eu

export LOG_LEVEL="DEBUG"
export PYTHONPATH='src'
pytest tests/unit --cov=src -vv
flake8 src
