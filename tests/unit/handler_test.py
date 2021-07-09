from src import handler
from unittest import TestCase
from unittest.mock import MagicMock
from unittest.mock import patch

# from handler import lambda_handler


class ContinueStepFunction(TestCase):
    def test_continues(self):
        auto_scaling_group_name = "mock_asg"
        instance_id = "mock_ec2_instance"
        lifecycle_hook_name = "hook_name"
        action = "CONTINUE"

        with patch("src.handler.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client

            event = {
                "ec2_instance_id": instance_id,
                "asg_name": auto_scaling_group_name,
                "lifecycle_hook_name": lifecycle_hook_name,
            }

            context = {"aws_request_id": "request_id"}

            handler.lambda_handler(event=event, context=context)

            mock_client.complete_lifecycle_action.assert_called_with(
                LifecycleHookName=lifecycle_hook_name,
                AutoScalingGroupName=auto_scaling_group_name,
                LifecycleActionResult=action,
                InstanceId=instance_id,
            )


# BELOW IS DONE WITH UNIT TEST
# from moto import mock_ec2

# we have an lambda handler returning the result - DONE
# we have a the instance ip - mocked
# we get a 200 when hitting the goss endpoint - mocked
# handler exit 1 if we dont get  200 return form the goss endpoint


# class HealthCheckTestCase(unittest.TestCase):
#     event = {"detail": {"EC2InstanceId": "i-0758ddb2bc1369045"}}
#
#     # @mock.patch("ec2_launch_checks_health_checks.get_instance_ip", return_value="1.1.1.1")
#     def test_lambda_handler_returns_event(self):
#         result = my_mod.lambda_handler(self.event)
#         self.assertIsInstance(result, dict)

# def test_get_instance_ip(self):
#     expected_result = "1.1.1.1"
#     result = my_mod.get_instance_ip("i-0758ddb2bc1369045")
#     self.assertEquals(result, expected_result)

# Wanted to mock this but boto does not currently cover describe instance
# @mock_ec2
# def test_get_intstance_ip_based_on_instance_id(self):
#     instance_id_1 = "i-0758ddb2bc1369045"
#     instance_id_2 = "i-0858ddb2bc7654321"

#     expected_result_1 = "2.2.2.2"
#     expected_result_2 = "3.3.3.3"

#     result_1 = my_mod.get_instance_ip(instance_id_1)
#     result_2 = my_mod.get_instance_ip(instance_id_2)

#     self.assertEquals(result_1, expected_result_1)
#     self.assertEquals(result_2, expected_result_2)
