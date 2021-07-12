import boto3
import pytest
import os

from botocore.stub import Stubber
from src.handler import lambda_handler
from src.handler import autoscaling_client
from src.exceptions import FailedToCompleteLifecycleActionException
from aws_lambda_context import LambdaContext


@pytest.fixture(autouse=True)
def autoscaling_stub():
    with Stubber(autoscaling_client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


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


def test_that_the_lambda_handler_succeeds_with_context_stubber(
    autoscaling_stub, asg_event, context
):
    # Arrange. complete_lifecycle_action has an empty response so we've tested the ResponseMetadata
    complete_lifecycle_action_expected_params = {
        "AutoScalingGroupName": "mock_asg",
        "InstanceId": "i-0123a456700123456",
        "LifecycleActionResult": "CONTINUE",
        "LifecycleHookName": "hook_name",
    }

    autoscaling_complete_lifecycle_action_valid = {
        "ResponseMetadata": {
            "HTTPHeaders": {
                "content-length": "294",
                "content-type": "text/xml",
                "date": "Tue, 23 Feb 2017 06:59:11 GMT",
                "x-amzn-requestid": "9b08345a-a01z-1234-1234-1234567ef20g",
            },
            "HTTPStatusCode": 200,
            "RequestId": "9b08345a-a01z-1234-1234-1234567ef20g",
            "RetryAttempts": 0,
        }
    }

    autoscaling_stub.activate()
    autoscaling_stub.add_response(
        "complete_lifecycle_action",
        expected_params=complete_lifecycle_action_expected_params,
        service_response=autoscaling_complete_lifecycle_action_valid,
    )

    # Act
    response = lambda_handler(asg_event, context)

    # Assert
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    autoscaling_stub.deactivate()


# we have an lambda handler returning the result - DONE
# we have a the instance ip - mocked
# we get a 200 when hitting the goss endpoint - mocked
# handler exit 1 if we dont get  200 return form the goss endpoint
