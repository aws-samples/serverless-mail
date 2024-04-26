import os
import boto3
import botocore
import hmac
import hashlib
import base64
import logging
import smtplib
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# These values are required to calculate the signature. Do not change them.
DATE = "11111111"
SERVICE = "ses"
MESSAGE = "SendRawEmail"
TERMINAL = "aws4_request"
VERSION = 0x04


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def calculate_key(sKey, region):

    signature = sign(("AWS4" + sKey).encode('utf-8'), DATE)
    signature = sign(signature, region)
    signature = sign(signature, SERVICE)
    signature = sign(signature, TERMINAL)
    signature = sign(signature, MESSAGE)
    signature_and_version = bytes([VERSION]) + signature
    smtp_password = base64.b64encode(signature_and_version)
    return smtp_password.decode('utf-8')


def create_secret(secret_client, secret_arn, token, smtp_iam_user_name, region):

    # Create new Access key and secret key
    iam_client = boto3.client('iam')
    new_key = iam_client.create_access_key(
        UserName=smtp_iam_user_name
    )

    new_access_key = new_key['AccessKey']['AccessKeyId']
    new_secret_key = new_key['AccessKey']['SecretAccessKey']

    new_smtp_secret = calculate_key(new_secret_key, region)
    new_secret = (f'{new_access_key}:{new_smtp_secret}')

    try:
        secret_client.put_secret_value(SecretId=secret_arn, ClientRequestToken=token, SecretString=new_secret, VersionStages=['AWSPENDING'])
    except botocore.exceptions.ClientError as error:

        print(error)
        print("Put secret failed, removing IAM key from user")
        iam_client.delete_access_key(
            UserName=smtp_iam_user_name,
            AccessKeyId=new_access_key
        )

        raise Exception("Secret couldn't be updated, removing IAM key pair")


def set_secret():

    # Nothing to do here
    return


def test_secret(secret_client, secret_arn, token, smtp_endpoint):

    # Get the pending secret
    pending_secret = secret_client.get_secret_value(SecretId=secret_arn, VersionId=token, VersionStage="AWSPENDING")['SecretString']

    secret_username, secret_password = pending_secret.split(":")

    # Create a new smtp client
    smtp_client = smtplib.SMTP_SSL(smtp_endpoint)

    # Re-try login attempts to give the new credential time to stabilise
    login_retry = 30
    successful = False

    # Loop with a delay to give the time for a credential to activate
    while login_retry != 0 and not successful:

        # Try a login to the server
        try:
            smtp_login = smtp_client.login(secret_username, secret_password)
        except:
            time.sleep(1)
            login_retry -= 1
            pass
        else:
            if smtp_login[0] == 235:
                successful = True

    if not successful:
        raise RuntimeError(f"Unable to login to smtp server : {smtp_login}")

    return


def finish_secret(secret_client, secret_arn, token, smtp_iam_user_name, document_name, server_key, server_key_value):

    # Get the current secret so we can delete based on access key later
    current_secret = secret_client.get_secret_value(SecretId=secret_arn)['SecretString']
    currentAccessKeyId = current_secret.split(":")[0]

    # Mark the pending secret as current
    _mark_new_secret_as_current(secret_client, secret_arn, token)

    # Get the new secret
    new_secret = secret_client.get_secret_value(SecretId=secret_arn)['SecretString']
    secret_username, secret_password = new_secret.split(":")

    ssm_client = boto3.client('ssm')
    # Execute the SSM command against the tagged servers with the new secret
    command_id = _execute_ssm_run_command(ssm_client, document_name, server_key, server_key_value, secret_username, secret_password)

    # Wait for invocations to appear for the command
    _wait_for_ssm_invocations(ssm_client, command_id)

    # Check all complete successfully
    _check_invocation_success(ssm_client, command_id)

    # Delete the old secret
    # Create an iam client
    iam_client = boto3.client('iam')
    iam_client.delete_access_key(
      UserName=smtp_iam_user_name,
      AccessKeyId=currentAccessKeyId
    )

    logger.info(f"finishSecret: Old IAM Key deleted for {smtp_iam_user_name}")


def _execute_ssm_run_command(ssm_client, document_name, server_key, server_key_value, secret_username, secret_password):
    # Execute the provided SSM document to update and restart the email server

    response = ssm_client.send_command(
      Targets=[
          {
              'Key': f"tag:{server_key}",
              'Values': [
                  server_key_value,
              ]
          },
      ],
      DocumentName=document_name,
      CloudWatchOutputConfig={
          'CloudWatchOutputEnabled': True
      },
      Parameters={
        'SESUsername': [
          secret_username,
        ],
        'SESPassword': [
          secret_password
        ]
      },
    )

    command_id = response['Command']['CommandId']
    logger.info(f"finishSecret: SSM Command ID {command_id} executed.")
    return command_id


def _wait_for_ssm_invocations(ssm_client, command_id):

    # list_command_invocations starts with returning 0 invocations and gradually adds them hence this logic
    invocationsFound = False
    retry = 10

    while not invocationsFound and retry > 0:

        if len(ssm_client.list_command_invocations(CommandId=command_id)['CommandInvocations']) > 0:
            invocationsFound = True
        else:
            time.sleep(0.5)
            retry -= 1

    if not invocationsFound:
        raise RuntimeError("SSM Document was not invoked on any instances, check the tags are set correctly")

    return


def _check_invocation_success(ssm_client, command_id):

    # Check all invocations complete, raise an error for those not successful
    invocationsComplete = False
    while not invocationsComplete:

        completeInvocations = 0

        command_invocation_status = ssm_client.list_command_invocations(CommandId=command_id)['CommandInvocations']
        for invocation in command_invocation_status:

            logger.info(f"finishSecret: Status of SSM Run Command on instance {invocation['InstanceId']} is {invocation['Status']}")
            if invocation['Status'] != 'Pending' and invocation['Status'] != 'InProgress':
                completeInvocations += 1

            # List isn't complete at first execution, this catches it growing
            totalInvocations = len(ssm_client.list_command_invocations(CommandId=command_id)['CommandInvocations'])

        if completeInvocations == totalInvocations:
            invocationsComplete = True
        else:
            time.sleep(5)

    # Raise an error if any were not successful
    command_invocation_status = ssm_client.list_command_invocations(CommandId=command_id)['CommandInvocations']
    invocationErrors = ""
    for invocation in command_invocation_status:
        if invocation['Status'] != 'Success':
            invocationErrors += f"SSM Invocation on host {invocation['InstanceId']}  {invocation['Status']}\n"

    if invocationErrors:
        raise RuntimeError(invocationErrors)

    return


def _mark_new_secret_as_current(secret_client, secret_arn, token):

    # First describe the secret to get the current version
    metadata = secret_client.describe_secret(SecretId=secret_arn)
    current_version = None
    for version in metadata["VersionIdsToStages"]:
        if "AWSCURRENT" in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info("finishSecret: Version %s already marked as AWSCURRENT for %s" % (version, secret_arn))
                return
            current_version = version
            break

    # Finalize by staging the secret version current
    secret_client.update_secret_version_stage(SecretId=secret_arn, VersionStage="AWSCURRENT", MoveToVersionId=token, RemoveFromVersionId=current_version)
    logger.info("finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s." % (token, secret_arn))

    return


def handler(event, context):

    logger.info(f"Received Event : {event}")

    # Get the event input values
    secret_arn = event['SecretId']
    token = event['ClientRequestToken']
    step = event['Step']

    # And the environment input details
    smtp_iam_user_arn = os.environ['SMTP_IAM_USER_NAME']
    smtp_endpoint = os.environ['SMTP_ENDPOINT']
    document_name = os.environ['SSM_ROTATION_DOCUMENT']
    server_key = os.environ['SSM_SERVER_TAG']
    server_key_value = os.environ['SSM_SERVER_TAG_VALUE']

    # Setup the client
    secret_client = boto3.client('secretsmanager')

    # Make sure the version is staged correctly
    metadata = secret_client.describe_secret(SecretId=secret_arn)
    if not metadata['RotationEnabled']:
        logger.error("Secret %s is not enabled for rotation" % secret_arn)
        raise ValueError("Secret %s is not enabled for rotation" % secret_arn)
    versions = metadata['VersionIdsToStages']
    if token not in versions:
        logger.error("Secret version %s has no stage for rotation of secret %s." % (token, secret_arn))
        raise ValueError("Secret version %s has no stage for rotation of secret %s." % (token, secret_arn))
    if "AWSCURRENT" in versions[token]:
        logger.info("Secret version %s already set as AWSCURRENT for secret %s." % (token, secret_arn))
        return
    elif "AWSPENDING" not in versions[token]:
        logger.error("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, secret_arn))
        raise ValueError("Secret version %s not set as AWSPENDING for rotation of secret %s." % (token, secret_arn))

    if step == "createSecret":
        logger.info("Executing Create Secret Function")
        region = os.environ['AWS_REGION']
        create_secret(secret_client, secret_arn, token, smtp_iam_user_arn, region)

    elif step == "setSecret":
        logger.info("Executing Set Secret Function")
        set_secret()

    elif step == "testSecret":
        logger.info("Executing Test Secret Function")
        test_secret(secret_client, secret_arn, token, smtp_endpoint)

    elif step == "finishSecret":
        logger.info("Executing Finish Secret Function")
        finish_secret(secret_client, secret_arn, token, smtp_iam_user_arn, document_name, server_key, server_key_value)

    else:
        raise ValueError("Invalid step parameter")
