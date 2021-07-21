#!/usr/bin/env python
import boto3
import json
import os
import requests

from aws_lambda_powertools import Logger
from botocore import exceptions

logger = Logger(
    service="aws-lambda-ec2-launch-checks",
    level=os.environ.get("LOG_LEVEL", "INFO"),
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
        private_ip_address = response["Reservations"][0]["Instances"][0][
            "PrivateIpAddress"
        ]
    except IndexError as e:
        raise FailedToGetPrivateIpAddressException(
            f"Instances list index out of range"
        ) from e
    except KeyError as e:
        raise FailedToGetPrivateIpAddressException(
            f"PrivateIpAddress field not found in ec2 describe instance response"
        ) from e

    return private_ip_address


def lambda_handler(event, context):
    logger.debug(f"Inside lambda_handler. event:{json.dumps(event)}")
    lifecycle_action_result = "CONTINUE"

    try:
        logger.info(f"Lambda Request ID: {context.aws_request_id}")
    except AttributeError as e:
        logger.error(e)
        raise FailedToLoadContextException(f"No context object available") from e

    try:
        # All three keys are required and should be present, raise KeyError if any are not supplied.
        auto_scaling_group_name = event["Payload"]["asg_name"]
        instance_id = event["Payload"]["ec2_instance_id"]
        lifecycle_hook_name = event["Payload"]["lifecycle_hook_name"]

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

    asg_specific_endpoint = "healthz"
    ip_address = get_instance_ip(instance_id)
    logger.debug(f"ip_address: {ip_address}")

    try:
        url = f"http://{ip_address}:9999/{asg_specific_endpoint}"
        logger.debug(f"Calling URL {url}")
        endpoint_call = requests.get(url)
        logger.info(f"Goss endpoint. Status Code: {endpoint_call.status_code}")
        logger.debug(f"Goss endpoint. Content: {endpoint_call.text}")
        if endpoint_call.status_code != 200:
            lifecycle_action_result = "ABANDON"
    except Exception as e:
        logger.error(f"Exception occurred while getting Goss results: {e}")
        raise FailedGossCheckException(
            f"Exception occurred while getting Goss results: {e}"
        )

    try:
        logger.debug(
            f"auto_scaling_group_name:{auto_scaling_group_name}, "
            f"auto_scaling_group_name: {auto_scaling_group_name}, "
            f"instance_id: {instance_id},"
            f"lifecycle_action_result:{lifecycle_action_result}, "
            f"lifecycle_hook_name:{lifecycle_hook_name}"
        )
        response = autoscaling_client.complete_lifecycle_action(
            AutoScalingGroupName=auto_scaling_group_name,
            InstanceId=instance_id,
            LifecycleActionResult=lifecycle_action_result,
            LifecycleHookName=lifecycle_hook_name,
        )
        logger.debug(f"Response of complete_lifecycle_action: {response}")
    except Exception as e:
        logger.error(e)
        raise FailedToCompleteLifecycleActionException(
            f"Caught exception when completing lifecycle action"
        ) from e

    # The return value has no use outside of the scope of this Lambda
    # Used in unit tests as a helpful check
    logger.info(f"Exiting lambda with {lifecycle_action_result}.")
    return lifecycle_action_result


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
