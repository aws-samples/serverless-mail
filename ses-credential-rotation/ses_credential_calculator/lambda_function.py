import logging
import hmac
import hashlib
import base64
import os

# Constants for SES SMTP password creation
DATE = "11111111"
SERVICE = "ses"
MESSAGE = "SendRawEmail"
TERMINAL = "aws4_request"
VERSION = 0x04

region = os.environ['AWS_REGION']

logger = logging.getLogger(__name__)


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


def handler(event, context):
    logger.info(event)
    access_key_id = event['AccessKeyId']
    secret_access_key = event['SecretAccessKey']
    smtp_password = calculate_key(secret_access_key, region)
    return f'{access_key_id}:{smtp_password}'
