#!/usr/bin/env python
import json
import os

import boto3
import requests
from aws_lambda_powertools import Logger
from botocore import exceptions

log_level = os.environ.get("LOG_LEVEL", "INFO")

logger = Logger(
    service="aws-lambda-ec2-launch-checks",
    level=log_level,
)

autoscaling_client = boto3.client(
    "autoscaling", region_name=os.environ.get("AWS_REGION", "eu-west-2")
)

ec2_client = boto3.client("ec2", region_name=os.environ.get("AWS_REGION", "eu-west-2"))


def get_instance_ip(instance_id: str) -> str:
    logger.debug(f"get_instance_ip for {instance_id}")
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
    except exceptions.ClientError as e:
        raise FailedToGetPrivateIpAddressException(
            f"EC2 Clients Describe Instances request failed with: {e.response['Error']['Message']}"
        ) from e

    logger.debug(f"ec2 describe_instances response: {response}")
    try:
        instance = response["Reservations"][0]["Instances"][0]
        network_interfaces = instance["NetworkInterfaces"]
        private_ip_address = instance["PrivateIpAddress"]

        if len(network_interfaces) > 1:
            logger.debug("Instance has extra network interface attached")
            for interface in network_interfaces:
                logger.debug("We will attempt to retrieve persistent private IP")
                if not interface["Attachment"]["DeleteOnTermination"]:
                    private_ip_address = interface["PrivateIpAddress"]

    except IndexError as e:
        raise FailedToGetPrivateIpAddressException(
            "Instances list index out of range"
        ) from e
    except KeyError as e:
        raise FailedToGetPrivateIpAddressException(
            "PrivateIpAddress field not found in ec2 describe instance response"
        ) from e

    return private_ip_address


def lambda_handler(event, context):
    logger.debug(f"Inside lambda_handler. event:{json.dumps(event)}")
    logger.info(f"Logging level: {log_level}")

    try:
        logger.info(f"Lambda Request ID: {context.aws_request_id}")
    except AttributeError as e:
        logger.error(e)
        raise FailedToLoadContextException("No context object available") from e

    try:
        # All three keys are required and should be present, raise KeyError if any are not supplied.
        auto_scaling_group_name = event["Payload"]["asg_name"]
        instance_id = event["Payload"]["ec2_instance_id"]
        lifecycle_hook_name = event["Payload"]["lifecycle_hook_name"]

        logger.append_keys(asg_name=auto_scaling_group_name)
        logger.append_keys(instance_id=instance_id)

        if not all([auto_scaling_group_name, instance_id, lifecycle_hook_name]):
            logger.error(f"Empty key in event: {json.dumps(event)}")
            raise MissingEventParamsException(
                f"Empty key in event: {json.dumps(event)}"
            )
    except KeyError as ke:
        logger.error(f"Missing key {ke} in event")
        raise FailedToLoadEventException(
            f"Missing key {ke} in event: {json.dumps(event)}"
        ) from ke
    except TypeError as te:
        logger.error(te)
        raise FailedToLoadEventException(
            f"Incorrect type passed to function: {te}"
        ) from te

    ip_address = get_instance_ip(instance_id)
    url = f"http://{ip_address}:9876/ec2-launch-checks"

    goss_test_pass = False
    try:
        logger.debug(f"Calling Goss endpoint: {url}")
        endpoint_call = requests.get(url, timeout=30)
        logger.info(f"Goss endpoint. Status Code: {endpoint_call.status_code}")
        logger.debug(f"Goss endpoint. Content: {endpoint_call.text}")
        if endpoint_call.status_code == 200:
            goss_test_pass = True

    except Exception as e:
        logger.error(f"Exception occurred while getting Goss results: {e}")
        raise FailedGossCheckException(
            f"Exception occurred while getting Goss results: {e}"
        )

    if not goss_test_pass:
        # Throwing an exception so step function will retry till Goss tests pass
        raise FailedGossCheckException("Goss check failed")

    try:
        logger.debug(
            f"auto_scaling_group_name:{auto_scaling_group_name}, "
            f"auto_scaling_group_name: {auto_scaling_group_name}, "
            f"instance_id: {instance_id},"
            f"lifecycle_hook_name:{lifecycle_hook_name}"
        )
        response = autoscaling_client.complete_lifecycle_action(
            AutoScalingGroupName=auto_scaling_group_name,
            InstanceId=instance_id,
            LifecycleActionResult="CONTINUE",
            LifecycleHookName=lifecycle_hook_name,
        )
        logger.debug(f"Response of complete_lifecycle_action: {response}")

    except exceptions.ClientError as e:
        err_code = e.response["Error"]["Code"]
        err_message = e.response["Error"]["Message"]
        if err_code == "ValidationError" and err_message.lower().startswith(
            "no active lifecycle action found"
        ):
            # Handle those instances become healthy and in service quickly
            is_instance_in_service = False
            logger.warning(err_message)
            logger.debug(f"Checking {instance_id} instance lifecycle state")
            response = autoscaling_client.describe_auto_scaling_instances(
                InstanceIds=[instance_id]
            )

            if len(response["AutoScalingInstances"]) == 1:
                instance = response["AutoScalingInstances"][0]
                if (
                    instance["InstanceId"] == instance_id
                    and instance["LifecycleState"] == "InService"
                    and instance["HealthStatus"] == "HEALTHY"
                ):
                    is_instance_in_service = True
                    logger.info(
                        f"Checked {instance_id} instance and it is healthy and in service"
                    )
                    logger.debug(instance)

            if not is_instance_in_service:
                message = f"Failed to mark the lifecycle as complete or confirm {instance_id} instance state"
                logger.error(message)
                logger.debug(response)
                raise FailedToCompleteLifecycleActionException(message) from e
        else:
            raise FailedToCompleteLifecycleActionException(
                "Caught exception when completing lifecycle action"
            ) from e
    except Exception as e:
        logger.error(e)
        raise FailedToCompleteLifecycleActionException(
            "Caught exception when completing lifecycle action"
        ) from e


class FailedGossCheckException(Exception):
    pass


class FailedToGetPrivateIpAddressException(Exception):
    pass


class FailedToCompleteLifecycleActionException(Exception):
    pass


class FailedToLoadContextException(Exception):
    pass


class FailedToLoadEventException(Exception):
    pass


class MissingEventParamsException(Exception):
    pass
