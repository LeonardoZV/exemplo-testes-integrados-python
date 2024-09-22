import os
import boto3
import json

sns_client = boto3.client('sns')


def lambda_handler(event, context):
    localstack = os.getenv("LOCALSTACK", False)
    topic_arn = "arn:aws:sns:us-west-1:000000000000:teste" if localstack else "aws"
    response = sns_client.publish(TopicArn=topic_arn, Message=json.dumps(event))
    return {'statusCode': 200, 'body': json.dumps(response, default=str)}
