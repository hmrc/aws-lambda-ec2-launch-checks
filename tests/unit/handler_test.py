import pytest
import os

from botocore.stub import Stubber
from src.handler import lambda_handler
from src.handler import autoscaling_client
from src.exceptions import (
    FailedToCompleteLifecycleActionException,
    FailedToLoadContextException,
    FailedToLoadEventException,
    MissingEventParamsException,
)
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
def valid_parameters():
    return {
        "AutoScalingGroupName": "mock_asg",
        "InstanceId": "i-0123a456700123456",
        "LifecycleActionResult": "CONTINUE",
        "LifecycleHookName": "hook_name",
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
    autoscaling_stub, asg_event, context, valid_parameters
):
    # Arrange. complete_lifecycle_action has an empty response so we've tested the ResponseMetadata
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
        expected_params=valid_parameters,
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


def test_that_the_lambda_handler_catches_complete_lifecycle_action_exception(
    autoscaling_stub, asg_event, context, valid_parameters
):
    # Arrange

    # Set up service error code
    service_error_code_expected = "ResourceContention"

    autoscaling_stub.activate()
    autoscaling_stub.add_client_error(
        "complete_lifecycle_action",
        expected_params=valid_parameters,
        service_error_code=service_error_code_expected,
    )

    # Act with raising the error
    with pytest.raises(FailedToCompleteLifecycleActionException) as error_message:
        response = lambda_handler(asg_event, context)

    # Assert. do we get the error message we want.
    assert "Caught exception when completing lifecycle action" in str(
        error_message.value
    )


def test_that_the_lambda_handler_catches_no_context_error(
    autoscaling_stub, asg_event, context
):
    # Arrange. complete_lifecycle_action has an empty response so we've tested the ResponseMetadata
    # Act with raising the error
    with pytest.raises(FailedToLoadContextException) as error_message:
        response = lambda_handler(asg_event, None)

    # Assert. do we get the error message we want.
    assert "No context object available" in str(error_message.value)


def test_that_the_lambda_handler_catches_bad_event_error(
    autoscaling_stub, asg_event, context
):
    # Arrange.  Bad event data
    bad_event = {
        "asg_name": "mock_asg",
        "lifecycle_hook_name": "hook_name",
    }
    # Act with raising the error
    with pytest.raises(MissingEventParamsException) as error_message:
        response = lambda_handler(bad_event, context)

    # Assert. do we get the error message we want.
    assert "Bad event object:" in str(error_message.value)


def test_that_the_lambda_handler_catches_none_event_error(
    autoscaling_stub, asg_event, context
):
    # Arrange.  Bad event data

    # Act with raising the error
    with pytest.raises(FailedToLoadEventException) as error_message:
        lambda_handler(None, context)

    # Assert. do we get the error message we want.
    assert "Unexpected error parsing event:" in str(error_message.value)
