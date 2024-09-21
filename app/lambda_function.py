import boto3
import os
import json

sns_client = boto3.client('sns')

def lambda_handler(event, context):

    response = sns_client.publish(TopicArn="arn:aws:sns:us-west-1:000000000000:teste", Message=json.dumps(event), Subject='Teste')

    return {'statusCode': 200, 'body': json.dumps(response, default=str)}