#!/usr/bin/env python
import boto3
import json
import logging
import os
import requests

from aws_lambda_powertools import Logger

# from src.exceptions import (
#     FailedToCompleteLifecycleActionException,
#     FailedToLoadContextException,
#     FailedToLoadEventException,
#     MissingEventParamsException,
# )

boto3.set_stream_logger(name="boto3", level=logging.DEBUG)


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


logger = Logger(
    service="aws-lambda-ec2-launch-checks",
    level=os.environ.get("LOG_LEVEL", "INFO"),
)

autoscaling_client = boto3.client(
    "autoscaling", region_name=os.environ.get("AWS_REGION", "eu-west-2")
)

ec2_client = boto3.client("ec2", region_name=os.environ.get("AWS_REGION", "eu-west-2"))


def get_instance_ip(instance_id: str) -> str:
    logger.info(f"get_instance_ip for {instance_id}")
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    logger.info(f"ec2 describe_instances response: {response}")
    try:
        private_ip_address = response["Reservations"][0]["Instances"][0][
            "PrivateIpAddress"
        ]
        if not private_ip_address:
            raise FailedToGetPrivateIpAddressException(f"PrivateIpAddress empty")
    except KeyError as e:
        raise FailedToGetPrivateIpAddressException(
            f"PrivateIpAddress field not found in ec2 describe instance response"
        ) from e

    return private_ip_address


def lambda_handler(event, context):
    logger.info(f"Inside lambda_handler. event:{json.dumps(event)}")
    lifecycle_action_result = "CONTINUE"

    try:
        logger.info(f"Lambda Request ID: {context.aws_request_id}")
    except AttributeError as e:
        logger.error(e)
        raise FailedToLoadContextException(f"No context object available") from e

    try:
        # All three keys are required and should be present, raise KeyError if any are not supplied.
        auto_scaling_group_name = event["asg_name"]
        instance_id = event["ec2_instance_id"]
        lifecycle_hook_name = event["lifecycle_hook_name"]

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
    ip_address = None

    try:
        ip_address = get_instance_ip(instance_id)
    except Exception as e:
        logger.error(e)

    logger.info(f"ip_address: {ip_address}")

    try:
        url = f"http://{ip_address}:9999/{asg_specific_endpoint}"
        logger.info(f"Calling URL {url}")
        endpoint_call = requests.get(url)
        logger.info(
            f"Goss endpoint. Status Code: {endpoint_call.status_code}, Content: {endpoint_call.text}"
        )

        if endpoint_call.status_code != 200:
            lifecycle_action_result = "ABANDON"
            raise FailedGossCheckException(
                f"Goss returned status code: {endpoint_call.status_code}"
            )

    except Exception as e:
        logger.error(e)

    try:
        # this is directing interacting with the asg. Should it instead return the LifecycleActionResult to
        # the stepfunction and the stepfuction pass that to the asg
        logger.info(
            f"auto_scaling_group_name:{auto_scaling_group_name}, "
            f"auto_scaling_group_name: {auto_scaling_group_name}, "
            f"instance_id@ {instance_id},"
            f"lifecycle_action_result:{lifecycle_action_result}, "
            f"lifecycle_hook_name:{lifecycle_hook_name}"
        )
        response = autoscaling_client.complete_lifecycle_action(
            AutoScalingGroupName=auto_scaling_group_name,
            InstanceId=instance_id,
            LifecycleActionResult=lifecycle_action_result,
            LifecycleHookName=lifecycle_hook_name,
        )
        logger.info(f"Response of complete_lifecycle_action: {response}")
    except Exception as e:
        logger.error(e)
        raise FailedToCompleteLifecycleActionException(
            f"Caught exception when completing lifecycle action"
        ) from e

    logger.info(f"Exiting lambda with return true.")
    return True
