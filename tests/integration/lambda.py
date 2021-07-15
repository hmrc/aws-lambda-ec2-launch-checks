import boto3
import botocore

# Set "running_locally" flag if you are running the integration test locally
running_locally = True

if running_locally:

    # Create Lambda SDK client to connect to appropriate Lambda endpoint
    lambda_client = boto3.client(
        "lambda",
        region_name="eu-west-2",
        endpoint_url="http://127.0.0.1:3001",
        use_ssl=False,
        verify=False,
        config=botocore.client.Config(
            signature_version=botocore.UNSIGNED,
            read_timeout=1,
            retries={"max_attempts": 0},
        ),
    )
else:
    lambda_client = boto3.client("lambda")


# Invoke your Lambda function as you normally usually do. The function will run
# locally if it is configured to do so
response = lambda_client.invoke(
    FunctionName="Ec2LaunchChecks",
    Payload='{"Payload": {"region": "eu-west-2", "lifecycle_hook_name": "elasticsearch-query-ec2-instance-launching-hook", "ec2_instance_id": "i-005cdef3a67d702c4", "asg_name": "elasticsearch-query"}}',
)

# Verify the response
assert response == "Hello World"
