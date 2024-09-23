import os
import json
import pytest
from testcontainers.localstack import LocalStackContainer
from testcontainers.core.labels import LABEL_SESSION_ID, SESSION_ID


def create_lambda_function(lambda_client, lambda_function_name):
    lambda_folder_path = os.path.abspath(os.path.dirname(__file__).replace("tests", "app"))
    response = lambda_client.create_function(
        FunctionName=lambda_function_name,
        Runtime='python3.12',
        Role='arn:aws:iam::000000000000:role/lambda-role',
        Handler='lambda_function.lambda_handler',
        Code={'S3Bucket': 'hot-reload', 'S3Key': lambda_folder_path}
    )
    lambda_client.get_waiter('function_active_v2').wait(FunctionName=lambda_function_name)
    return response['FunctionArn']


def create_sns_topic(sns_client, sns_topic_name):
    response = sns_client.create_topic(Name=sns_topic_name)
    return response['TopicArn']


def create_sqs_queue(sqs_client, queue_name):
    queue_url = sqs_client.create_queue(QueueName=queue_name)['QueueUrl']
    queue_arn = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['QueueArn'])['Attributes']['QueueArn']
    return queue_url, queue_arn


def subscribe_sqs_to_sns(sns_client, topic_arn, queue_arn):
    sns_client.subscribe(TopicArn=topic_arn, Protocol='sqs', Endpoint=queue_arn)


@pytest.mark.filterwarnings("ignore:datetime.datetime.utcnow")
def test_lambda_function():
    # Arrange
    localstack = (LocalStackContainer(image="localstack/localstack:latest", region_name="us-east-1")
                  .with_services("lambda", "sns", "sqs")
                  .with_env("LAMBDA_RUNTIME_IMAGE_MAPPING", '{"python3.12": "public.ecr.aws/lambda/python:3.12"}')
                  # SESSION_ID NECESSARIO PARA QUE O LAMBDA CONTAINER SEJA EXCLUIDO AUTOMATICAMENTE.
                  # É UM BUG QUE FOI CONCERTADO NA LIB JAVA (https://github.com/localstack/localstack/issues/8616).
                  # MAS AINDA CORRIGIDO NÃO NA LIB PYTHON.
                  .with_env("LAMBDA_DOCKER_FLAGS", f"-l {LABEL_SESSION_ID}={SESSION_ID}")
                  # NECESSARIO PARA QUE O LAMBDA CONTAINER SEJA CRIADO AUTOMATICAMENTE.
                  .with_volume_mapping("/var/run/docker.sock", "/var/run/docker.sock", "rw"))

    with localstack as localstack:
        
        lambda_client = localstack.get_client("lambda")
        sns_client = localstack.get_client("sns")
        sqs_client = localstack.get_client("sqs")

        function_name = "teste"
        topic_name = "teste"
        queue_name = "teste"

        create_lambda_function(lambda_client, function_name)
        topic_arn = create_sns_topic(sns_client, topic_name)
        queue_url, sqs_queue_arn = create_sqs_queue(sqs_client, queue_name)
        subscribe_sqs_to_sns(sns_client, topic_arn, sqs_queue_arn)

        input = {"bla": "blab"}

        # Act
        lambda_response = lambda_client.invoke(FunctionName=function_name, Payload=json.dumps(input).encode())

        sqs_response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=5)
        messages = sqs_response.get('Messages', [])
        messages_dict = [json.loads(json.loads(message["Body"])["Message"]) for message in messages]

        # Assert
        assert input in messages_dict
