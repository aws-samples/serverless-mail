import boto3
from urllib.parse import quote


def handler(event, context):
    print(f'Received event {event}')

    inputEvent = event['ExecutionContext']['Execution']['Input']
    server = inputEvent['Server']
    apigwEndpoint = inputEvent['APIGWEndpoint']
    secretLocation = inputEvent['SecretLocation']
    snsTopic = inputEvent['ConfirmationEmailSNSTopic']

    taskToken = event['ExecutionContext']['Task']['Token']

    confirmationLink = apigwEndpoint + "/execution?action=confirm&taskToken=" + quote(taskToken)

    client = boto3.client("sns")

    emailMessage = "Hello\n\n"
    emailMessage += f"This is an email to notify you that the AWS SES SMTP credential on host {server} requires rotation.\n"
    emailMessage += f"A new credential has been created as part of this workflow and is accessible from : {secretLocation}\n\n"
    emailMessage += f"Once the credential has been rotated and tested on {server}, please use the following link to confirm the rotation has been completed successfully : {confirmationLink}\n"
    emailMessage += "Once all credentials have been rotated, the old credential will be de-activated and deleted."

    emailSubject = f"AWS SES SMTP credential rotation required on {server}"

    client.publish(
        TopicArn=snsTopic,
        Subject=emailSubject,
        Message=emailMessage
    )
