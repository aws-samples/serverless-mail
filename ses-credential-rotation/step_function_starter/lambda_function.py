import boto3
import os
import datetime


def handler(event, context):
    print(f'Received event from source: {event.get("source", "unknown")}')

    stepFunctionArn = os.environ['StepFunctionArn']
    currentDate = datetime.datetime.now()

    client = boto3.client("stepfunctions")

    client.start_execution(
        stateMachineArn=stepFunctionArn,
        name=f'SESCredentialRotation-{currentDate.year}{currentDate.month:02d}{currentDate.day:02d}'
    )

    return
