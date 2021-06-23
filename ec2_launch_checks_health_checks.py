#!/usr/bin/env python
import boto3
import requests

print("Loading function health_checks_lambda")


def get_instance_ip(instance_id: str) -> str:
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["PrivateIpAddress"]


def lambda_handler(event, context) -> dict:
    # stepfunction:
    # get_instance_ip -> [ip address] -> health_check
    asg_specific_endpoint = "healthz"

    event["ip_address"] = get_instance_ip(event["detail"]["EC2InstanceId"])

    endpoint_call = requests.get(f"https://{event['detail']['ip_address']}:9999/{asg_specific_endpoint}")
    event["response_code"] = endpoint_call.status_code

    if endpoint_call.status_code == 200:
        raise RuntimeError(f"health check endpoint for {event['detail']['ip_address']} did not return 200")
    return event
