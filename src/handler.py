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
    logger.info(f"response: {response}")
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
    auto_scaling_group_name = None
    instance_id = None
    lifecycle_action_result = "CONTINUE"
    lifecycle_hook_name = None

    try:
        logger.info(f"Paul Lambda Request ID: {context.aws_request_id}")
    except AttributeError as e:
        logger.error(e)
        # Disabling the throwing of exceptions as we don't want the instance to terminate (yet)
        # raise FailedToLoadContextException(f"No context object available") from e

    try:
        logger.info(json.dumps(event))
        payload = event.get("Payload")
        logger.info(f"payload: {payload}")
        auto_scaling_group_name = payload.get("asg_name")
        instance_id = payload.get("ec2_instance_id")
        lifecycle_hook_name = payload.get("lifecycle_hook_name")

        if not all([auto_scaling_group_name, instance_id, lifecycle_hook_name]):
            raise MissingEventParamsException(f"Bad event object: {json.dumps(event)}")
    except AttributeError as e:
        logger.error(e)
        # Disabling the throwing of exceptions as we don't want the instance to terminate (yet)
        # raise FailedToLoadEventException(
        #     f"Unexpected error parsing event: {json.dumps(event)}"
        # ) from e

    asg_specific_endpoint = "healthz"
    ip_address = None

    try:
        ip_address = get_instance_ip(instance_id)
    except Exception as e:
        logger.error(e)

    logger.info(f"ip_address: {ip_address}")

    try:
        endpoint_call = requests.get(
            f"https://{ip_address}:9999/{asg_specific_endpoint}"
        )

        if endpoint_call.status_code == 200:
            lifecycle_action_result = "CONTINUE"
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
    except Exception as e:
        logger.error(e)
        # Disabling the throwing of exceptions as we don't want the instance to terminate (yet)
        # raise FailedToCompleteLifecycleActionException(
        #     f"Caught exception when completing lifecycle action"
        # ) from e

    return True
