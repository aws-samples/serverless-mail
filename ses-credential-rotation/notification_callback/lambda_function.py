import boto3
import json


def handler(event, context):
    print(f'Received event {event}')

    token = event['query']['taskToken']

    client = boto3.client("stepfunctions")

    message = {"Status": "Credential Rotation Confirmed"}

    client.send_task_success(
        taskToken=token,
        output=json.dumps(message)
    )

    responsePage = "<html><head>Confirmation Received</head><body><p>"
    responsePage += "Thankyou - We have updated the confirmation status "
    responsePage += "for this server</body></html>"

    return responsePage
