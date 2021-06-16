#!/usr/bin/env python
from __future__ import print_function
import boto3
import random


print('Loading function get_instance_ip')


def get_instance_ip(instance_id):
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response['Reservations'][0]['Instances'][0]['PrivateIpAddress']


def lambda_handler(event, context):
    """
    Entrypoint for the lambda.
    This lambda will populate the ip address of the given instance, and add a
    random_wait field with a random wait between 10 and 360.
    :param event: dictionary passed in as input to the lambda. It must contain at
                  least a 'detail' field with another dictionary inside, containing
                  a 'EC2InstanceId' with the id of the instance we are interested on.
    """
    event['ip_address'] = get_instance_ip(event['detail']['EC2InstanceId'])
    event['random_wait'] = random.randint(10, 360)
    print('Instance IP is {}'.format(event['ip_address']))
    return event
