SHELL := /usr/bin/env bash
POETRY_OK := $(shell type -P poetry)
POETRY_PATH := $(shell poetry env info --path)
POETRY_REQUIRED := $(shell cat .poetry-version)
POETRY_VIRTUALENVS_IN_PROJECT ?= true
PYTHON_OK := $(shell type -P python)
PYTHON_REQUIRED := $(shell cat .python-version)
PYTHON_VERSION ?= $(shell python -V | cut -d' ' -f2)
ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

BUCKET_NAME := telemetry-internal-base-lambda-artifacts
LAMBDA_NAME := aws-lambda-ec2-launch-checks
TELEMETRY_INTERNAL_BASE_ACCOUNT_ID := 634456480543

help: ## The help text you're reading
	@grep --no-filename -E '^[a-zA-Z1-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

assemble: clean ## Build the lambda zip file using Docker
	@./bin/lambda-tools.sh assemble
.PHONY: assemble

bandit: ## Run bandit against python code
	@poetry run bandit -r ./src -c .bandit
.PHONY: bandit

black: ## Run black against python code
	@poetry run black ./src ./tests
.PHONY: black

black_check: ## Show changes black would make
	@poetry run black --check --diff ./src ./tests
.PHONY: black_check

check_poetry: check_python ## Check Poetry installation
    ifeq ('$(POETRY_OK)','')
	    $(error package 'poetry' not found!)
    else
	    @echo Found Poetry ${POETRY_REQUIRED}
    endif
.PHONY: check_poetry

check_python: ## Check Python installation
    ifeq ('$(PYTHON_OK)','')
	    $(error python interpreter: 'python' not found!)
    else
	    @echo Found Python
    endif
    ifneq ('$(PYTHON_REQUIRED)','$(PYTHON_VERSION)')
	    $(error incorrect version of python found: '${PYTHON_VERSION}'. Expected '${PYTHON_REQUIRED}'!)
    else
	    @echo Found Python ${PYTHON_REQUIRED}
    endif
.PHONY: check_python

clean: ## Teardown build artefacts
	@rm -rf ./build ./venv ./venv_assemble
.PHONY: clean

cut_release: ## Cut release
	@./bin/lambda-tools.sh cut_release
.PHONY: cut_release

debug_env: ## Print out variables used by lambda-tools.sh
	@./bin/lambda-tools.sh debug_env
.PHONY: debug_env

package: ## Run a Docker build to assemble the lambda zip file
	@./bin/lambda-tools.sh assemble
.PHONY: package

prepare_release: ## Runs prepare release
	@./bin/lambda-tools.sh prepare_release
.PHONY: prepare_release

publish: ## Build and push lambda zip to S3 (requires MDTP_ENVIRONMENT to be set to an environment)
	@./bin/lambda-tools.sh publish
.PHONY: publish

safety: ## Run Safety
	@poetry run safety check
.PHONY: safety

setup: check_poetry ## Setup virtualenv & dependencies using poetry and set-up the git hook scripts
	@export POETRY_VIRTUALENVS_IN_PROJECT=$(POETRY_VIRTUALENVS_IN_PROJECT) && poetry run pip install --upgrade pip
	@poetry install --no-root
	@poetry run pre-commit install
.PHONY: setup

sh: ## Start an interactive session in the Python container
	@./bin/lambda-tools.sh open_shell
.PHONY: sh

test: ## Run unit tests
	@./bin/lambda-tools.sh unittest
.PHONY: test

verify: setup test bandit black safety ## Run all the checks and tests
.PHONY: verify

verify_package_and_publish: verify prepare_release publish cut_release ## Run all the checks and tests, assemble, and then publish the lambda
.PHONY: verify_package_and_publish
