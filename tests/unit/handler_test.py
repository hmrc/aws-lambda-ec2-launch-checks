import pytest
import os

from src.handler import lambda_handler
from src.exceptions import FailedToCompleteLifecycleActionException
from aws_lambda_context import LambdaContext
from unittest.mock import patch, Mock


@patch("boto3.client")
def test_that_the_lambda_handler_succeeds_with_context(
    mock_boto_client, asg_event, context
):
    # Arrange/Act
    response = lambda_handler(event=asg_event, context=context)

    # Assert
    mock_boto_client().complete_lifecycle_action.assert_called_once_with(
        LifecycleHookName=asg_event.get("lifecycle_hook_name"),
        AutoScalingGroupName=asg_event.get("asg_name"),
        LifecycleActionResult="CONTINUE",
        InstanceId=asg_event.get("ec2_instance_id"),
    )
    assert response == "RETURN"


def test_api(asg_event, context):
    # boto_error = FailedToCompleteLifecycleActionException("Boo")
    # mock_client = Mock(**{"complete_lifecycle_action.side_effect": boto_error})
    # mock_boto_client.complete_lifecycle_action.side_effect = FailedToCompleteLifecycleActionException('Boom!')
    with patch('boto3.client.complete_lifecycle_action', side_effect=Exception):
        with pytest.raises(Exception) as exception_info:
            response = lambda_handler(event=asg_event, context=context)

    assert "Caught exception when completing lifecycle action: Boom!" in str(exception_info.value)


@patch("src.handler.boto3.client")
def test_that_the_lambda_handler_catches_attribute_error(
    mock_boto_client, asg_event, context
):
    # Arrange
    mock_boto_client.complete_lifecycle_action.side_effect = FailedToCompleteLifecycleActionException('Boom!')
    # with patch('boto3.client.complete_lifecycle_action', side_effect=FailedToCompleteLifecycleActionException('mocked error')):
    with pytest.raises(FailedToCompleteLifecycleActionException) as exception_info:
        response = lambda_handler(event=asg_event, context=context)

    # Assert
    assert "Caught exception when completing lifecycle action: Boom!" in str(exception_info.value)


@pytest.fixture(scope="function")
def asg_event():
    return {
        "ec2_instance_id": "i-0123a456700123456",
        "asg_name": "mock_asg",
        "lifecycle_hook_name": "hook_name",
    }


@pytest.fixture(scope="function")
def context():
    lambda_context = LambdaContext()
    lambda_context.function_name = "lambda_handler"
    lambda_context.aws_request_id = "abc-123"
    return lambda_context


@pytest.fixture(autouse=True)
def initialise_environment_variables():
    os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "eu-west-2"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


####
# class ContinueStepFunction(TestCase):
#     def test_continues(self):
#         auto_scaling_group_name = "mock_asg"
#         instance_id = "mock_ec2_instance"
#         lifecycle_hook_name = "hook_name"
#         action = "CONTINUE"
#
#         with patch("src.handler.boto3") as mock_boto3:
#             mock_client = MagicMock()
#             mock_boto3.client.return_value = mock_client
#
#             event = {
#                 "ec2_instance_id": instance_id,
#                 "asg_name": auto_scaling_group_name,
#                 "lifecycle_hook_name": lifecycle_hook_name,
#             }
#
#             context = {"aws_request_id": "request_id"}
#
#             handler.lambda_handler(event=event, context=context)
#
#             mock_client.complete_lifecycle_action.assert_called_with(
#                 LifecycleHookName=lifecycle_hook_name,
#                 AutoScalingGroupName=auto_scaling_group_name,
#                 LifecycleActionResult=action,
#                 InstanceId=instance_id,
#             )


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
