#!/usr/bin/env bash

set -eu

export LOG_LEVEL="DEBUG"
export PYTHONPATH='src'
pytest tests/unit --ruff --no-cov-on-fail --cov=src -vv
