#!/bin/bash

set -eu

export LOG_LEVEL="DEBUG"
export PYTHONPATH='src'
pytest tests/unit --cov=src
flake8 src/handler.py
