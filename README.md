
# aws-lambda-ec2-launch-checks

[![Brought to you by Telemetry Team](https://img.shields.io/badge/MDTP-Telemetry-40D9C0?style=flat&labelColor=000000&logo=gov.uk)](https://confluence.tools.tax.service.gov.uk/display/TEL/Telemetry)

* Triggered by an Auto Scaling Lifecycle hook when launching an instance.
* This Lambda checks the Goss end point of the instance and if the Goss tests pass the Lifecycle hook is completed.
* Enabled in Terraform by the flag: `enable_health_check_hook = true`

Please check the [telemetry-terraform](https://github.com/hmrc/telemetry-terraform) repository for details on how this Lambda is deployed.

## Requirements

* [Python 3.8+](https://www.python.org/downloads/release)
* [Poetry](https://python-poetry.org/)

## Quick start

```shell
# Install correct version of Python
pyenv install $(cat .python-version)

# Optional set up environment variables
export POETRY_VIRTUALENVS_IN_PROJECT=true
export PYTHONPATH=/home/paul/work_repos/aws-lambda-ec2-launch-checks
export MDTP_ENVIRONMENT=internal-base

# Run tests:
make test

# Package the lambda locally:
make package
```

### Environment variables
The following environment variables are processed by the lambda handler and can therefore be set in Terraform to
override the defaults provided:

* `AWS_REGION` (default: "eu-west-2")
* `LOG_LEVEL` (default: "INFO")

### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").

# References


### License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
