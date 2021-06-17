SHELL := /usr/bin/env bash
ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
WEBOPS_INTEGRATION_ACCOUNT_ID := 150648916438
S3_BUCKET_NAME := mdtp-lambda-functions-integration

help: ## The help text you're reading
	@grep --no-filename -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

package: ## Build the lambdas
	@mkdir -p build/deps
	@poetry export -f requirements.txt --without-hashes -o build/deps/requirements.txt
	@pip install --target build/deps -r build/deps/requirements.txt
	@mkdir -p build/artifacts

	# ec2_launch_checks_get_instance_ip lambda
	@rm -f build/artifacts/ec2_launch_checks_get_instance_ip.zip
	@zip -r build/artifacts/ec2_launch_checks_get_instance_ip.zip ec2_launch_checks_get_instance_ip.py
	@cd build/deps && zip -r ../artifacts/ec2_launch_checks_get_instance_ip.zip . && cd -
	@openssl dgst -sha256 -binary build/artifacts/ec2_launch_checks_get_instance_ip.zip | openssl enc -base64 > build/artifacts/ec2_launch_checks_get_instance_ip.zip.base64sha256

	# ec2_launch_checks_health_checks lambda
	@rm -f build/artifacts/ec2_launch_checks_health_checks.zip
	@zip -r build/artifacts/ec2_launch_checks_health_checks.zip ec2_launch_checks_health_checks.py
	@cd build/deps && zip -r ../artifacts/ec2_launch_checks_health_checks.zip . && cd -
	@openssl dgst -sha256 -binary build/artifacts/ec2_launch_checks_health_checks.zip | openssl enc -base64 > build/artifacts/ec2_launch_checks_health_checks.zip.base64sha256
.PHONY: package

publish: ## Push lambdas zip to S3
	@if [ "$$(aws sts get-caller-identity | jq -r .Account)" != "${WEBOPS_INTEGRATION_ACCOUNT_ID}" ]; then \
  		echo "Please make sure that you execute this target with a \"webops-integration\" AWS profile. Exiting."; exit 1; fi

	# ec2_launch_checks_get_instance_ip lambda
	@aws s3 cp build/artifacts/ec2_launch_checks_get_instance_ip.zip s3://${S3_BUCKET_NAME}/ec2_launch_checks_get_instance_ip.zip --acl=bucket-owner-full-control
	@aws s3 cp build/artifacts/ec2_launch_checks_get_instance_ip.zip.base64sha256 s3://${S3_BUCKET_NAME}/ec2_launch_checks_get_instance_ip.zip.base64sha256 --content-type text/plain --acl=bucket-owner-full-control

	# ec2_launch_checks_health_checks lambda
	@aws s3 cp build/artifacts/ec2_launch_checks_health_checks.zip s3://${S3_BUCKET_NAME}/ec2_launch_checks_health_checks.zip --acl=bucket-owner-full-control
	@aws s3 cp build/artifacts/ec2_launch_checks_health_checks.zip.base64sha256 s3://${S3_BUCKET_NAME}/ec2_launch_checks_health_checks.zip.base64sha256 --content-type text/plain --acl=bucket-owner-full-control
.PHONY: publish
