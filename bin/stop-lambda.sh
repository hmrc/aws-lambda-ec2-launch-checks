#!/usr/bin/env bash

# The script should only be executed _within_ the context of a
# poetry run command e.g.
# poetry run task stop-lambda
# or
# poetry run bin/stop-lambda.sh

set -ue

kill -9 "$(cat build/sam-lambda-runner.pid)"
rm build/sam-lambda-runner.pid
echo "Lambda function stopped."
