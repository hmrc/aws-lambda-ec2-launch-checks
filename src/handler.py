#!/usr/bin/env python
import boto3
import json
import os
from aws_lambda_powertools import Logger
from src.exceptions import FailedToCompleteLifecycleActionException

logger = Logger(
    service="aws-lambda-ec2-launch-checks",
    level=os.environ.get("LOG_LEVEL", "INFO"),
)

autoscaling_client = boto3.client(
    "autoscaling", region_name=os.environ.get("AWS_REGION", "eu-west-2")
)


def lambda_handler(event, context):
    auto_scaling_group_name = ""
    instance_id = ""
    lifecycle_action_result = "CONTINUE"
    lifecycle_hook_name = ""

    try:
        logger.info(f"Lambda Request ID: {context.aws_request_id}")
    except AttributeError:
        logger.debug(f"No context object available")

    try:
        logger.debug(json.dumps(event))
        auto_scaling_group_name = event.get("asg_name")
        instance_id = event.get("ec2_instance_id")
        lifecycle_hook_name = event.get("lifecycle_hook_name")
    except AttributeError:
        print(f"Unable to find ec2/asg details in event")

    try:
        response = autoscaling_client.complete_lifecycle_action(
            AutoScalingGroupName=auto_scaling_group_name,
            InstanceId=instance_id,
            LifecycleActionResult=lifecycle_action_result,
            LifecycleHookName=lifecycle_hook_name,
        )
    except Exception as e:
        message = f"Caught exception when completing lifecycle action: {e}"
        logger.error(message)
        raise FailedToCompleteLifecycleActionException(message)

    return response


# import requests

# def get_instance_ip(instance_id: str) -> str:
#     ec2 = boto3.client("ec2")
#     response = ec2.describe_instances(InstanceIds=[instance_id])
#     return response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]

#     # stepfunction:
#     # get_instance_ip -> [ip address] -> health_check
#     asg_specific_endpoint = "healthz"
#
#     event["ip_address"] = get_instance_ip(event["detail"]["EC2InstanceId"])
#
#     endpoint_call = requests.get(f"https://{event['detail']['ip_address']}:9999/{asg_specific_endpoint}")
#     event["response_code"] = endpoint_call.status_code
#
#     if endpoint_call.status_code == 200:
#         raise RuntimeError(f"health check endpoint for {event['detail']['ip_address']} did not return 200")
