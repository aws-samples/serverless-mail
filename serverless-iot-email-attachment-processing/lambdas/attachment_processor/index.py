import email
import json
import os
import tempfile
from typing import List
from email.message import Message
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import utils as email_utils
import boto3
from aws_lambda_powertools import Logger, Tracer
from botocore.exceptions import ClientError

logger = Logger(level=os.getenv("LOG_LEVEL", "INFO"))
tracer = Tracer()

client_s3 = boto3.client("s3")
client_sns = boto3.client("sns")

# Define AWS region in a Lambda environment variable
INCOMING_EMAIL_BUCKET = os.environ["INCOMING_BUCKET"]
OUTPUT_BUCKET = os.environ["ATTACHMENTS_BUCKET"]
PRESIGNED_EXPIRATION = int(os.environ["PRESIGNED_EXPIRATION"])
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
EMAIL_REGEX_CODE = os.environ["EMAIL_REGEX_CODE"]
SNS_TOPIC = os.environ["SNS_TOPIC"]


@tracer.capture_method
def get_message_from_s3(bucket_name, bucket_key) -> dict:
    """
    Get the email object from the S3 bucket.
    :param bucket_name:  name of the S3 bucket SES stores emails it receives
    :param bucket_key: S3 bucket key where SES places the emails it receives (not used in the proof of concept)
    :return:
    """
    object_s3 = client_s3.get_object(Bucket=bucket_name, Key=bucket_key)
    # Read the content of the message.
    file = object_s3["Body"].read()

    file_dict = {"file": file, "bucket": bucket_name, "bucket_key": bucket_key}

    return file_dict


@tracer.capture_method
def get_attachment_from_s3_eml_file(mail_object: Message, attachment_prefix: str) -> List[str]:
    """
    Parses the .eml file from S3 for the first attachment, stores the attachment in an S3 bucket for that
    purpose, generates a pre-signed URL to it, and returns the pre-signed URL or empty string
    REQUIRES 2 env variables:
        'bucket_name_for_email_attachments' - S3 bucket where Lambda stores attachments
        'expiration_presigned_urls' - number of seconds the pre-signed URL is accessible (36hrs used in PoC)
    :param mail_object:
    :param attachment_prefix:
    :return: []
    """

    # Determine if the email is multipart, if so then find the first attachment and store in a temp file,
    #  if not then return empty string
    presigned_urls = []

    if not mail_object.is_multipart():
        logger.info("email is NOT Multi-part- i.e. plain text, no attachments")
        return presigned_urls

    for part in mail_object.walk():
        cdispo = str(part.get("Content-Disposition"))
        # skip any text/plain (txt) attachments
        if "attachment" in cdispo:
            filename = part.get_filename()
            attachment_key = f"{attachment_prefix}/{filename}"
            # write the file to path tmp_filepath
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(part.get_payload(decode=True))
                fp.seek(0)
                client_s3.upload_file(fp.name, OUTPUT_BUCKET, attachment_key)

                # Generate a presigned_url for the attachment file now stored in the attachments S3 bucket
                presigned_url = create_presigned_url(
                    OUTPUT_BUCKET, attachment_key, PRESIGNED_EXPIRATION, client_s3
                )
                presigned_urls += [presigned_url]

    return presigned_urls


# Parses the .eml file from S3 for the email body, adds line breaks, and returns it as a string
@tracer.capture_method
def get_body_from_s3_eml_file(mail_object: Message) -> str:
    # Process the email message to get the body content as a string - index 0 is the email body
    email_body = mail_object.get_payload(0).get_payload()
    # Check if  get_payload is returning a list for some reason
    if isinstance(email_body, list):
        s = ''.join(str(email_body))
        s = s.replace("\n", "<br />\n")
        return s
    return email_body


# Get the Subject from the .eml file in S3
@tracer.capture_method
def get_email_from_s3_event(event) -> (Message, str):
    # Get the objectKey and send as a parameter to get_message_from_s3
    bucket_key = event["Records"][0]["s3"]["object"]["key"]  # filename
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]  # filename

    file_dict = get_message_from_s3(bucket_name, bucket_key)

    # Process the email message to get the subject content as a string and return it
    mail_object = email.message_from_string(file_dict["file"].decode("utf-8"))
    email_prefix = os.path.basename(bucket_key)

    return mail_object, email_prefix


# Creates a MIME multipart message object, using the Python `email` standard library.
#    :param sender: The sender's email address as a string.
#    :param recipients: List of recipients. Needs to be a list, even if only one recipient.
#    :param title: The subject of the email.
#    :param text: The text version of the email body (WILL BE IGNORED).
#    :param html: The html version of the email body (optional).
#    :param attachment: A file to attach in the email.
#    :return: A `MIMEMultipart` to be used to send the email.
@tracer.capture_method
def create_multipart_message(
    sender: str,
    recipients: list,
    title: str,
    text: str = None,
    html: str = None,
    attachment: str = None,
    attachment_type: str = None,
) -> MIMEMultipart:
    multipart_content_subtype = "alternative" if text and html else "mixed"
    msg = MIMEMultipart(multipart_content_subtype)
    msg["Subject"] = title
    msg["From"] = sender
    msg["To"] = ",".join(recipients)

    # Record the MIME type part text/html ONLY, text/plain will be ignored.
    # According to RFC 2046, the last part of a multipart message, in this case the HTML message, is best and preferred.
    if html:
        part = MIMEText(html, "html")
        msg.attach(part)

    if attachment_type == "file":
        # Add attachments
        with open(attachment, "rb") as f:
            part = MIMEApplication(f.read())
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(attachment),
            )
            msg.attach(part)

    return msg


# Returns dictionary containing 1) comma-delimited string with all email addr's found in the email body
#   following a specific code matching the Email_Rxers_Code environment variable and 2) the email body
#   with the codes and email addresses removed
#   REQUIRES 1 env variable: 'Email_Rxers_Code' - used by SMTP client admins to prepend and append a
#   comma-delimited string with all email addr's in the email body
@tracer.capture_method
def get_email_addrs_from_body(email_body: str) -> dict:
    # Get env var matching code the admin inserts into each SMTP message preceding a list of email addresses

    # walk through email body to find line with the code then set email_addrs_list to rest of line and break
    email_addrs_list = ""
    begin = email_body.find(EMAIL_REGEX_CODE) + len(EMAIL_REGEX_CODE)
    end = email_body.find(EMAIL_REGEX_CODE, begin)

    # Leave it empty if both beginning and end codes are not found
    if begin > -1 and end > -1:
        email_addrs_list = email_body[begin:end]

    # Remove the code and email addresses list from the email body
    remove_str = EMAIL_REGEX_CODE + email_addrs_list
    email_body = email_body.replace(remove_str, "")
    email_body = email_body.replace(EMAIL_REGEX_CODE, "")

    # Remove all whitespace characters (space, tab, newline, and so on) from the email_addrs_list
    email_addrs_list = "".join(email_addrs_list.split())
    email_addrs_list = email_addrs_list.replace("<br />", "")
    email_addrs_list = email_addrs_list.replace("<br/>", "")

    # Return the email addresses list and the email body with the code and addresses list removed
    return {"email_addrs_list": email_addrs_list, "email_body": email_body}


# Sends one mail from sender email address, to all recipients, with title as email subject, body either
#   text or html strings, and with attachment (if provided)
@tracer.capture_method
def send_mail(
    sender: str,
    recipients: list,
    title: str,
    text: str = None,
    html: str = None,
    attachment: str = None,
    attachment_type: str = None,
) -> dict:
    ses_client = boto3.client("ses")
    msg = create_multipart_message(
        sender, recipients, title, text, html, attachment, attachment_type
    )
    logger.info("sending raw email")
    return ses_client.send_raw_email(
        Source=sender, Destinations=recipients, RawMessage={"Data": msg.as_string()}
    )


# Returns a presigned URL for the S3 object specified in bucket_name with expiration
#   :param bucket_name: string
#   :param object_name: string
#   :param expiration: Time in seconds for the presigned URL to remain valid
#   :return: Presigned URL as string. If error, returns None.
@tracer.capture_method
def create_presigned_url(
    bucket_name: str, object_name: str, expiration: int, s3_client: object
) -> str:
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_name,
            },
            ExpiresIn=expiration,
        )

    # Handles exception
    except ClientError as e:
        logger.error(f"Unable to sign url for {bucket_name}/{object_name}")
        return None

    # The response contains the presigned URL
    return response
    

# Main handler of the Lambda function, triggered by S3 object PUT which should be a .eml file from SES
#   REQUIRES 1 env variable: 'SENDER_EMAIL' - the "From:" address in the email sent to the end user
@tracer.capture_lambda_handler
@logger.inject_lambda_context
def lambda_handler(event, context):
    # Get the SES MAIL-FROM address from a Lambda environment variable, error out if empty
    (_, parsed_email) = email_utils.parseaddr(SENDER_EMAIL)
    if not parsed_email or parsed_email == "":
        logger.error(
            "Please provide sender email address. The provided sender value is {}".format(
                SENDER_EMAIL
            )
        )
        return

    response = {}
    success = True
    records = event.get("Records", [])
    record = None
    if records:
        record = records[0]

    if record:
        message_id = record["messageId"]
        status, message = handle_incoming_record(json.loads(record["body"]), context)
        response = {"messageId": message_id, "status": status, message: message}
        success = status and success

    status_code = 200 if success else 500

    return {"statusCode": status_code, "body": json.dumps(response)}


def handle_incoming_record(event, context):
    sender_ = SENDER_EMAIL

    text_ = ""  # text/plain email is not used in this Proof of Concept

    # Get the email subject from the S3 .eml file PUT in the bucket by SES
    email_subject: Message
    attachment_prefix: str
    mail_object, attachment_prefix = get_email_from_s3_event(event)
    title_ = mail_object["Subject"]

    # Get the email body from the S3 .eml file PUT in the bucket by SES
    body_ = get_body_from_s3_eml_file(mail_object)

    # Set email recipients to the email addresses listed in the SMTP email body after specific code
    #   and remove the codes & email addresses from the email body
    email_body_recipients_dict = get_email_addrs_from_body(body_)
    # Convert the comma delimited string of email addresses to a List
    recipients_ = email_body_recipients_dict["email_addrs_list"].split(",")
    body_ = email_body_recipients_dict["email_body"]

    # Generate a shortened, pre-signed URL for the first attachment in the email and add it to the end of
    # the email body sent to the end-users; if no attachments exist then do nothing
    presigned_url_array = get_attachment_from_s3_eml_file(mail_object, attachment_prefix)

    # Step through all presigned_urls in the array, shorten each, and place on a new line
    all_urls = ""
    for url in presigned_url_array:
        all_urls = all_urls + url + "<br />"
    
    body_ = (
        body_
        + "The original email included one or more attachments which we've stored for you here: "
        + all_urls
    )
    # If the SMTP client email body didn't provide a coded list of user email addresses then
    #   set email recipients to the email addresses in the appropriate SES Contacts List (admins)
    if "@" not in str(recipients_):
        body_ = (
            body_
            + "ERROR! No receiver email addresses coded into the email body. Please adjust SMTP client settings."
        )

        payload = {
            "attachment": "",
            "attachment_type": "",
            "body": body_,
            "recipients": recipients_,
            "sender": sender_,
            "title": title_,
        }

        payload_message = json.dumps(payload)
        result = client_sns.publish(TopicArn=SNS_TOPIC, Message=payload_message)
        logger.warning(
            "Incoming message did not have expected recipient list, forwarding to fallback topic.",
            extra={
                "email_id": attachment_prefix,
                "sns_message_id": result.get("MessageId", "")
            }
        )
        return

    # Send empty strings as attachment & attachment_type because we're removing the attachment and appending
    #   a pre-signed URL into the body instead
    try:
        response_ = send_mail(
            sender_,
            recipients_,
            title_,
            text_,
            body_,
            attachment="",
            attachment_type="",
        )
        logger.info(response_)
        return True, response_
    except Exception as e:
        logger.error(f"Unable to send email, ref: {attachment_prefix}")
        return False, ""
