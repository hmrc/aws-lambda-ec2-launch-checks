#!/usr/bin/env bash

# Because this is a blocking operation we can't call it directly
# as a taskipy task, so it has been outsourced to this script.

# The script should only be executed _within_ the context of a
# poetry run command e.g.
# poetry run task start-lambda
# or
# poetry run bin/start-lambda.sh

set -ue

sam local start-lambda --debug 2>&1 &
echo $! > build/sam-lambda-runner.pid
sleep 5 # Ensure the Lambda is started before returning back to the caller.
echo "Lambda function started."
