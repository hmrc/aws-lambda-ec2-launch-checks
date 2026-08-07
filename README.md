# aws-lambda-ec2-launch-checks

[![Brought to you by Telemetry Team](https://img.shields.io/badge/MDTP-Telemetry-40D9C0?style=flat&labelColor=000000&logo=gov.uk)](https://confluence.tools.tax.service.gov.uk/display/TEL/Telemetry)

* Triggered by an Auto Scaling Lifecycle hook when launching an instance.
* This Lambda checks the Goss end point of the instance and if the Goss tests pass the Lifecycle hook is completed.
* Enabled in Terraform by the flag: `enable_health_check_hook = true`

## Table of Contents
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [License](#license)

<!-- END doctoc -->

## Prerequisites

* [mise](https://mise.jdx.dev/) to manage tool versions and integrates with `uv`.
* [uv](https://docs.astral.sh/uv/) to manage Python virtual environments and dependencies.

## Quick start

Install dependencies using uv:

```shell
mise run setup
# Run tests:
mise run test
# Package the lambda locally:
mise run package
```

## License

This code is open source software licensed under the [Apache 2.0 License]("http://www.apache.org/licenses/LICENSE-2.0.html").
