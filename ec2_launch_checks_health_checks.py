#!/usr/bin/env python
from __future__ import print_function


print("Loading function health_checks_lambda")


def lambda_handler(event, context):
    # stepfunction:
    # get_instance_ip -> [ip address] -> health_check

    # event['ip_address'] = event['detail']['ip_address']
    # response = request.get(f"{ip_address}/{asg_specific_endpoint})
    # return response_code == 200
    # event['response_code'] = response.code
    return event
