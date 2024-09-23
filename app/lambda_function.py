import os
import boto3
import json

sns_client = boto3.client('sns')


def lambda_handler(event, context):
    AWS_REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    AWS_ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID", "000000000000")
    topic_arn = f"arn:aws:sns:{AWS_REGION}:{AWS_ACCOUNT_ID}:teste"
    response = sns_client.publish(TopicArn=topic_arn, Message=json.dumps(event))
    return {'statusCode': 200, 'body': json.dumps(response, default=str)}
