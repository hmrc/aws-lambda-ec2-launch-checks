import pytest
import os
import requests

from aws_lambda_context import LambdaContext
from botocore.stub import Stubber

from src.handler import lambda_handler
from src.handler import autoscaling_client
from src.handler import ec2_client
from src.handler import get_instance_ip
from src.handler import (
    FailedGossCheckException,
    FailedToCompleteLifecycleActionException,
    FailedToGetPrivateIpAddressException,
    FailedToLoadContextException,
    FailedToLoadEventException,
    MissingEventParamsException,
)


@pytest.fixture(autouse=True)
def autoscaling_stub():
    with Stubber(autoscaling_client) as stubber:
        stubber.activate()
        yield stubber
        stubber.deactivate()
        stubber.assert_no_pending_responses()


@pytest.fixture(autouse=True)
def ec2_stub():
    with Stubber(ec2_client) as stubber:
        stubber.activate()
        yield stubber
        stubber.deactivate()
        stubber.assert_no_pending_responses()


@pytest.fixture(scope="function")
def ec2_response():
    return {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0123a456700123456",
                        "PrivateIpAddress": "10.1.3.1",
                    }
                ]
            }
        ]
    }


@pytest.fixture(scope="function")
def ec2_response_empty_instances_array():
    return {"Reservations": [{"Instances": []}]}


@pytest.fixture(scope="function")
def asg_event():
    return {
        "Payload": {
            "ec2_instance_id": "i-0123a456700123456",
            "asg_name": "mock_asg",
            "lifecycle_hook_name": "hook_name",
        }
    }


@pytest.fixture(scope="function")
def ec2_response_with_no_ipaddress():
    return {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0123a456700123456",
                    }
                ]
            }
        ]
    }


@pytest.fixture(scope="function")
def autoscaling_complete_lifecycle_action_valid_parameters():
    return {
        "AutoScalingGroupName": "mock_asg",
        "InstanceId": "i-0123a456700123456",
        "LifecycleActionResult": "CONTINUE",
        "LifecycleHookName": "hook_name",
    }


@pytest.fixture(scope="function")
def autoscaling_complete_lifecycle_action_valid_abandon_parameters():
    return {
        "AutoScalingGroupName": "mock_asg",
        "InstanceId": "i-0123a456700123456",
        "LifecycleActionResult": "ABANDON",
        "LifecycleHookName": "hook_name",
    }


@pytest.fixture(scope="function")
def context():
    lambda_context = LambdaContext()
    lambda_context.function_name = "lambda_handler"
    lambda_context.aws_request_id = "abc-123"
    return lambda_context


def valid_goss_content():
    return (
        "Service: logstash: running: matches expectation: [true]\n\n\n"
        "Total Duration: 0.093s\nCount: 1, Failed: 0, Skipped: 0\n"
    )


@pytest.fixture(scope="function")
def autoscaling_complete_lifecycle_action_response_valid():
    return {
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


def test_goss_succeeds_completes_lifecycle_action(
    ec2_stub,
    autoscaling_stub,
    ec2_response,
    asg_event,
    context,
    autoscaling_complete_lifecycle_action_valid_parameters,
    autoscaling_complete_lifecycle_action_response_valid,
    requests_mock,
):
    # Arrange
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response,
    )

    autoscaling_stub.add_response(
        "complete_lifecycle_action",
        expected_params=autoscaling_complete_lifecycle_action_valid_parameters,
        service_response=autoscaling_complete_lifecycle_action_response_valid,
    )

    requests_mock.get(f"http://10.1.3.1:9999/healthz", text=valid_goss_content())

    # Act
    lambda_handler(asg_event, context)

    # Assert


def test_that_the_lambda_handler_catches_complete_lifecycle_action_exception(
    ec2_stub,
    autoscaling_stub,
    ec2_response,
    asg_event,
    context,
    autoscaling_complete_lifecycle_action_valid_parameters,
    requests_mock,
):
    # Arrange
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response,
    )

    requests_mock.get(f"http://10.1.3.1:9999/healthz", text=valid_goss_content())

    # Set up service error code
    service_error_code_expected = "ResourceContention"

    autoscaling_stub.add_client_error(
        "complete_lifecycle_action",
        expected_params=autoscaling_complete_lifecycle_action_valid_parameters,
        service_error_code=service_error_code_expected,
    )

    # Act
    with pytest.raises(FailedToCompleteLifecycleActionException) as error_message:
        lambda_handler(asg_event, context)

    # Assert
    assert "Caught exception when completing lifecycle action" in str(
        error_message.value
    )


def test_that_the_lambda_handler_catches_no_context_error(
    autoscaling_stub, asg_event, context
):
    # Act with no context
    with pytest.raises(FailedToLoadContextException) as error_message:
        lambda_handler(asg_event, None)

    # Assert
    assert "No context object available" in str(error_message.value)


def test_that_the_lambda_handler_catches_bad_event_error(
    autoscaling_stub, asg_event, context
):
    # Arrange
    bad_event = {
        "Payload": {
            "asg_name": "mock_asg",
            "lifecycle_hook_name": "hook_name",
        }
    }
    # Act
    with pytest.raises(FailedToLoadEventException) as error_message:
        lambda_handler(bad_event, context)

    # Assert
    assert "Missing key 'ec2_instance_id'" in str(error_message.value)


def test_that_the_lambda_handler_catches_none_event_error(
    autoscaling_stub, asg_event, context
):
    # Act with no event
    with pytest.raises(FailedToLoadEventException) as error_message:
        lambda_handler(None, context)

    # Assert
    assert (
        "Incorrect type passed to function: 'NoneType' object is not subscriptable"
        in str(error_message.value)
    )


def test_that_the_lambda_handler_catches_event_with_empty_key(
    autoscaling_stub, asg_event, context
):
    # Arrange
    bad_event = {
        "Payload": {
            "asg_name": "mock_asg",
            "ec2_instance_id": "",
            "lifecycle_hook_name": "hook_name",
        }
    }
    # Act
    with pytest.raises(MissingEventParamsException) as error_message:
        lambda_handler(bad_event, context)

    # Assert
    assert "Empty key in event:" in str(error_message.value)


def test_get_instance_ip_valid(ec2_stub, ec2_response):
    # Arrange
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response,
    )

    # Act
    response = get_instance_ip("i-0123a456700123456")

    # Assert
    assert response == "10.1.3.1"


def test_get_instance_ip_raises_clienterror(
    ec2_stub, ec2_response_empty_instances_array
):
    # Arrange
    ec2_stub.add_client_error(
        "describe_instances",
        service_error_code="InvalidInstanceID.NotFound",
        service_message="The instance ID 'i-0123a456700123456' does not exist",
        http_status_code=400,
    )

    # Act
    with pytest.raises(FailedToGetPrivateIpAddressException) as error_message:
        get_instance_ip("i-0123a456700123456")

    # Assert.
    assert "EC2 Clients Describe Instances request failed with" in str(
        error_message.value
    )


def test_get_instance_ip_with_empty_instance_array(
    ec2_stub, ec2_response_empty_instances_array
):
    # Arrange
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response_empty_instances_array,
    )

    # Act
    with pytest.raises(FailedToGetPrivateIpAddressException) as error_message:
        get_instance_ip("i-0123a456700123456")

    # Assert.
    assert "Instances list index out of range" in str(error_message.value)


def test_get_instance_ip_with_empty_instance_array_no_ipaddress(
    ec2_stub, ec2_response_with_no_ipaddress
):
    # Arrange
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response_with_no_ipaddress,
    )

    # Act
    with pytest.raises(FailedToGetPrivateIpAddressException) as error_message:
        get_instance_ip("i-0123a456700123456")

    # Assert.
    assert "PrivateIpAddress field not found in ec2 describe instance response" in str(
        error_message.value
    )


def test_goss_returns_error_throws_exception(
    ec2_stub,
    ec2_response,
    asg_event,
    context,
    requests_mock,
):
    # Arrange.
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response,
    )

    requests_mock.get(f"http://10.1.3.1:9999/healthz", status_code=500)

    # Act
    with pytest.raises(FailedGossCheckException) as error_message:
        lambda_handler(asg_event, context)

    # Assert. do we get the error message we want.
    assert "Goss check failed" in str(error_message.value)


def test_goss_connection_timeout_throws_exception(
    ec2_stub,
    ec2_response,
    asg_event,
    context,
    requests_mock,
):
    # Arrange.
    ec2_stub.add_response(
        "describe_instances",
        service_response=ec2_response,
    )

    requests_mock.get(
        f"http://10.1.3.1:9999/healthz", exc=requests.exceptions.ConnectTimeout
    )

    # Act
    with pytest.raises(FailedGossCheckException) as error_message:
        lambda_handler(asg_event, context)

    # Assert
    assert "Exception occurred while getting Goss results:" in str(error_message.value)
