import boto3
import logging
import hmac
import hashlib
import base64
import os
from crhelper import CfnResource

# Constants for SES SMTP password creation
DATE = "11111111"
SERVICE = "ses"
MESSAGE = "SendRawEmail"
TERMINAL = "aws4_request"
VERSION = 0x04

region = os.environ['AWS_REGION']

logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(json_logging=False, log_level='DEBUG', boto_level='CRITICAL', sleep_on_delete=120, ssl_verify=None)

try:
    ssm_client = boto3.client('ssm')
except Exception as e:
    helper.init_failure(e)


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def calculate_key(secret_access_key, region):

    signature = sign(("AWS4" + secret_access_key).encode('utf-8'), DATE)
    signature = sign(signature, region)
    signature = sign(signature, SERVICE)
    signature = sign(signature, TERMINAL)
    signature = sign(signature, MESSAGE)
    signature_and_version = bytes([VERSION]) + signature
    smtp_password = base64.b64encode(signature_and_version)
    return smtp_password.decode('utf-8')


def create_parameter_store_secret(secret_name, secret, key):

    kwargs = dict(
        Name=secret_name,
        Description='Secrect for AWS SES SMTP Mail sending',
        Value=secret,
        Type='SecureString',
    )

    if key != "None":

        kwargs["KeyId"] = key

    ssm_client.put_parameter(
        **kwargs
    )
    return


def delete_parameter_store_secret(secret_name):

    try:
        ssm_client.delete_parameter(
            Name=secret_name
        )
    except ssm_client.exceptions.ParameterNotFound:
        pass


@helper.create
def create(event, context):
    logger.info("Got Create")

    secret_username = event['ResourceProperties']['SecretUsername']
    secret_password = event['ResourceProperties']['SecretPassword']
    secret_name = event['ResourceProperties']['SecretName']
    key = event['ResourceProperties']['KMSKey']

    logger.info("Generating Secret value")
    secret_string = secret_username + ":" + calculate_key(secret_password, region)

    print('Adding secret to Parameter Store')
    create_parameter_store_secret(secret_name, secret_string, key)
    return None


@helper.update
def update(event, context):
    logger.info("Got Update")

    raise Exception("Sorry, this template does not support a CloudFormation Update")

    return None


@helper.delete
def delete(event, context):
    logger.info("Got Delete")

    secret_name = event['ResourceProperties']['SecretName']

    logger.info("Deleting Secret value")

    print('Deleting secret from Parameter Store')
    delete_parameter_store_secret(secret_name)

    return None


def handler(event, context):
    logger.info(event)
    helper(event, context)
