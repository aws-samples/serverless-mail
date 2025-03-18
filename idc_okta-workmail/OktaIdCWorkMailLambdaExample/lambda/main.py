import logging
import random
import string
from os import getenv
from typing import Generator, List, Dict

import botocore.exceptions
from botocore.config import Config
from botocore.client import BaseClient
from botocore.session import Session

LOG_LEVEL = getenv("LOG_LEVEL", "INFO").upper()
IDENTITYSTORE_ID = getenv("IDENTITYSTORE_ID", None)
IDENTITY_CENTER_INSTANCE_ARN = getenv("IDENTITY_CENTER_INSTANCE_ARN", None)
IDENTITY_CENTER_APPLICATION_ARN = getenv("IDENTITY_CENTER_APPLICATION_ARN", None)
WORKMAIL_ORGANIZATION_ID = getenv("WORKMAIL_ORGANIZATION_ID", None)
OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL = getenv("OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL", None)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

BOTO_CONFIG = Config(
    region_name = "us-east-1",
    retries = {
        'max_attempts': 4, # Maximum number of retries
        'mode': 'adaptive', # Exponential backoff strategy
        'total_max_attempts': 5,  # Total attempts including the initial call
    }
)

MAX_SIZE = 100
DEFAULT_DOMAIN_KEY = "DefaultMailDomain"

# Script will describe organization and use default domain to enable users and assign email address to them
# If you want to override this behavior and use different domain, change it in the config accordingly.
# Note, you need to register domain first in the WorkMail using Console or APIs.
# Example:
# CONFIG = {
#   DEFAULT_DOMAIN_KEY: "my-not-default-domain.com",
# }
CONFIG = {}


def get_client(service_name: str) -> BaseClient:
    """Creating boto3 client for provided service.

    :param service_name:
    :return:
    """
    session = Session()
    client = session.create_client(service_name, config=BOTO_CONFIG)
    return client


def get_identity_center_application_arn(workmail_client: BaseClient, organization_id: str) -> str:
    """Querying IdentityCenter application id for WorkMail organization.

    :param workmail_client: WorkMail boto3 client
    :param organization_id: WorkMail organization Id
    :return: string with IdentityCenter application id
    """
    try:
        response = workmail_client.describe_identity_provider_configuration(OrganizationId=organization_id)
        return response['IdentityCenterConfiguration']['ApplicationArn']
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error describing organization: {e}")
        raise e
    except KeyError as e:
        logger.error(f"No ApplicationArn found. "
                     f"Check that you have enabled IdentityCenter integration with WorkMail: {e}")
        raise e


def list_group_membership(identitystore_client: BaseClient, identity_store_id: str, group_id: str) -> Generator[str, None, None]:
    """Querying IdentityCenter group membership

    :param identitystore_client: IdentityStore boto3 client.
    :param identity_store_id: IdentityStore Id.
    :return: Generator where each iteration yields IdentityCenter UserId
    """
    logger.info(f"Querying group membership from IdentityCenter")
    counter = 0
    try:
        next_token = None

        while True:
            params = {
                'IdentityStoreId': identity_store_id,
                'GroupId': group_id,
                'MaxResults': MAX_SIZE
            }
            if next_token:
                params['NextToken'] = next_token

            response = identitystore_client.list_group_memberships(**params)
            logger.info(f"Got {len(response['GroupMemberships'])} group memberships from IdentityCenter")

            for group_membership in response['GroupMemberships']:
                counter += 1
                yield group_membership["MemberId"]["UserId"]

            if 'NextToken' in response:
                next_token = response['NextToken']
            else:
                break

    except botocore.exceptions.ClientError as e:
        logger.error(f"Error listing group memberships: {e}")
        raise e
    finally:
        logger.info(f"Queried {counter} members of group {group_id} from IdentityCenter")


def describe_idc_user(identitystore_client: BaseClient, identity_store_id: str, user_id: str) -> Dict[str, str]:
    """Querying IdentityCenter users

    :param user_id:
    :param identitystore_client: IdentityStore boto3 client.
    :param identity_store_id: IdentityStore Id.
    :return: Generator where each iteration yields dictionary with IdentityCenter user info
    """
    logger.info(f"Describing user {user_id} from IdentityCenter")
    params = {
        'IdentityStoreId': identity_store_id,
        'UserId': user_id,
    }

    try:
        response = identitystore_client.describe_user(**params)
        logger.info(f"Got User {response['UserId']} from IdentityCenter")
        return response

    except botocore.exceptions.ClientError as e:
        logger.error(f"Error describing user: {e}")
        raise e


def generate_password() -> string:
    digits = random.sample(string.digits, 5)
    ascii = random.sample(string.ascii_letters, 5)
    special = random.sample("!@#$%^&*()", 2)

    return "".join(digits + ascii + special)


def get_workmail_users(workmail_client: BaseClient, organization_id: str) -> Generator[dict, None, None]:
    logger.info(f"Querying users from WorkMail")
    counter = 0
    try:
        next_token = None
        while True:
            params = {
                'OrganizationId': organization_id,
                'MaxResults': MAX_SIZE
            }
            if next_token:
                params['NextToken'] = next_token

            response = workmail_client.list_users(**params)
            logger.info(f"Got {len(response['Users'])} users from WorkMail")

            for user in response['Users']:
                counter += 1
                if user["State"] != "DELETED":
                    yield user

            if 'NextToken' in response:
                next_token = response['NextToken']
            else:
                break

    except botocore.exceptions.ClientError as e:
        logger.error(f"Error listing users: {e}")
        raise e
    finally:
        logger.info(f"Queried {counter} users from WorkMail")


def get_differences(idc_users: Generator[str, None, None], workmail_users: Generator[dict, None, None]) -> Dict[str, List]:
    """Comparing 2 sets of users based on username and IdentityCenterId existence in WorkMail user.
    returns a dictionary of users to create and users to disable in WorkMail

    :param idc_users:
    :param workmail_users:
    :return:
    """
    workmail_users_to_create = []
    workmail_users_to_enable = []
    workmail_users_to_disable = []
    workmail_users_dict = {item["IdentityProviderUserId"]: item for item in workmail_users}
    idc_users_set = set(idc_users)

    logger.info(f"Trying to find differences between WorkMail and IdC")
    for user_id in idc_users_set:
        # If user exists in IdC but not in WorkMail, we need to create it in WorkMail
        if user_id not in workmail_users_dict:
            workmail_users_to_create.append(user_id)

    logger.info(f"Found {len(workmail_users_to_create)} users to create in WorkMail")

    for idc_user_id, item in workmail_users_dict.items():
        # If user exists in WorkMail but not in IdC we need to disable it in WorkMail
        if idc_user_id not in idc_users_set and workmail_users_dict[idc_user_id]["State"] != "DISABLED":
            workmail_users_to_disable.append(item)
        # If user exists in IdC, but it has status is "DISABLED" in WorkMail we need to enable it in WorkMail
        elif workmail_users_dict[idc_user_id]["State"] == "DISABLED":
            workmail_users_to_enable.append(item)

    logger.info(f"Found {len(workmail_users_to_enable)} users to enable in WorkMail")
    logger.info(f"Found {len(workmail_users_to_disable)} users to disable in WorkMail")

    return {
        "create": workmail_users_to_create,
        "disable": workmail_users_to_disable,
        "enable": workmail_users_to_enable,
    }

def clean_idc_username(username: str) -> str:
    """Removes domain from username if it exists.

    :param username: IdentityCenter Username
    :return: Username without domain (localpart)
    """
    splitted = username.split("@")
    return splitted[0] if len(splitted) > 1 else username


def get_default_domain(workmail_client: BaseClient, organization_id: str) -> str:
    """Querying default domain for WorkMail organization.

    :param workmail_client: WorkMail boto3 client
    :param organization_id: WorkMail organization Id
    :return: string with default domain
    """
    if DEFAULT_DOMAIN_KEY in CONFIG:
        return CONFIG[DEFAULT_DOMAIN_KEY]

    response = workmail_client.describe_organization(OrganizationId=organization_id)
    CONFIG[DEFAULT_DOMAIN_KEY] = response['DefaultMailDomain']
    return CONFIG[DEFAULT_DOMAIN_KEY]


def create_workmail_user(workmail_client: BaseClient, organization_id: str, user: dict) -> bool:
    """Creates user in WorkMail. If user already exists, it will be skipped. If user is not associated with IdC,
    it will be logged as an error but script will continue it's work.

    :param workmail_client: WorkMail boto3 client
    :param organization_id: WorkMail organization Id
    :param user: IdentityCenter user structure
    :return: True | False
    """
    logger.info(f"Creating user {user['UserName']} in WorkMail organization {organization_id}")

    try:
        response = workmail_client.create_user(
            OrganizationId=organization_id,
            Name=user['UserName'],
            DisplayName=user['DisplayName'],
            Password=generate_password(), # backwards compatibility
            IdentityProviderUserId=user['UserId']
        )
        logger.info(f"Created user {user['UserName']} in WorkMail with UserId: {response['UserId']}")

        # By default, all new users are disabled.
        # We are enabling users by registering them using default organization domain.
        enable_workmail_user(workmail_client, organization_id, response["UserId"], user["UserName"])

    except workmail_client.exceptions.NameAvailabilityException:
        logger.info(f"User {user['UserName']} already exists in WorkMail. Skipping")
        return False
    except workmail_client.exceptions.InvalidParameterException as e:
        error_message = e.response['Error']['Message']
        if "is not authorized" in error_message:
            # All users should have assignment to WorkMail application before they could be associated.
            # To Create assignment use AWS CLI: `aws sso-admin create-application-assignment` or
            # assign users through IdentityCenter page in WorkMail console.
            # This is not a code error
            logger.error(f"Error creating IdC user {user['UserName']} in WorkMail."
                         f" Please check if user has assignment to WorkMail application")
            return False
        else:
            # This could be a code error
            raise e
    return True


def disable_workmail_user(workmail_client: BaseClient, organization_id: str, user: dict):
    """Disables user in WorkMail.

    :param workmail_client:
    :param WORKMAIL_ORGANIZATION_ID:
    :param user:
    :return:
    """
    logger.info(f"Disabling user {user['Name']} in WorkMail organization {WORKMAIL_ORGANIZATION_ID}")
    try:
        workmail_client.deregister_from_work_mail(
            OrganizationId=WORKMAIL_ORGANIZATION_ID,
            EntityId=user['Id'],
        )
        logger.info(f"Disabled user {user['Name']} in WorkMail")
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error disabling user {user['Name']} in WorkMail: {e}")
        return False
    return True


def enable_workmail_user(workmail_client: BaseClient, organization_id: str, user_id: str, user_name: str):
    """Enabling user in WorkMail.

    :param user_name:
    :param user_id:
    :param workmail_client:
    :param organization_id:
    :param user:
    :return:
    """

    # By default, all new users are disabled.
    # We are enabling users by registering them using default organization domain.
    default_domain = get_default_domain(workmail_client, organization_id)
    localpart = clean_idc_username(user_name)
    user_email = f"{localpart}@{default_domain}"

    logger.info(f"Registering user {user_name} to WorkMail with email: {user_email}")

    try:
        workmail_client.register_to_work_mail(
            OrganizationId=organization_id,
            EntityId=user_id,
            Email=user_email,
        )
        logger.info(f"Successfully registered user {user_name} with email {user_email} in WorkMail")
    except botocore.exceptions.ClientError as e:
        logger.error(f"Error enabling user {user_name} in WorkMail: {e}")
        return False
    return True


def main():
    """Entrypoint for the script. It will query IdentityCenter users and based on them create users in WorkMail.
    """
    logger.info("Starting script")
    # Making use of automatic assume role credentials via profile in ~/.aws/credentials
    # Creating clients
    logger.info(f"Creating clients")
    identitystore_client = get_client('identitystore')
    ssoadmin_client = get_client('sso-admin')
    workmail_client = get_client('workmail')

    # Checking if IdC integration is enabled in WorkMail and
    # application ARN is the same in script and in the WorkMail config.
    if get_identity_center_application_arn(workmail_client, WORKMAIL_ORGANIZATION_ID) != IDENTITY_CENTER_APPLICATION_ARN:
        raise Exception("IdentityCenter Application ARN configured in WorkMail is not the same as in script settings")

    # For each created WorkMail user we will put IdentityCenter user id in IdentityProviderUserId field.
    # This will create an association between IdentityCenter and WorkMail user.
    # However, IdentityCenter user must be assigned to WorkMail first (user must be allowed to log in through IdC
    # to WorkMail)
    # We will do this assignment automatically based on IdentityCenter group Id provided in the config

    logger.info(f"Creating assignment for group {OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL} in WorkMail")
    ssoadmin_client.create_application_assignment(
      ApplicationArn=IDENTITY_CENTER_APPLICATION_ARN,
      PrincipalId=OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL,
      PrincipalType="GROUP"
    )

    # Lazy initialization of query functions
    idc_users = list_group_membership(identitystore_client, IDENTITYSTORE_ID, OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL)
    workmail_users = get_workmail_users(workmail_client, WORKMAIL_ORGANIZATION_ID)

    # checking differences between WorkMail and IdentityCenter users
    differences = get_differences(idc_users, workmail_users)

    successful_creation = 0
    for user_id in differences["create"]:
        user = describe_idc_user(identitystore_client, IDENTITYSTORE_ID, user_id)
        try:
            successful_creation += create_workmail_user(workmail_client, WORKMAIL_ORGANIZATION_ID, user)
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error creating IdC user {user['UserName']} in WorkMail: {e}")
            continue

    logger.info(f"Created {successful_creation} users in WorkMail")

    successful_disabling = 0
    for user in differences["disable"]:
        successful_disabling += disable_workmail_user(workmail_client, WORKMAIL_ORGANIZATION_ID, user)

    logger.info(f"Disabled {successful_disabling} users in WorkMail")

    successful_enabling = 0
    for user in differences["enable"]:
        successful_enabling += enable_workmail_user(workmail_client, WORKMAIL_ORGANIZATION_ID,
                                                    user["Id"], user["Name"])

    logger.info(f"Enabled {successful_enabling} in WorkMail")

    # We do not raise exception for each failed attempt, trying to synchronize as much as we can.
    # However, if we have at least single error, we are making it visible for lambda, failing the whole execution
    if (successful_creation != len(differences["create"])) or \
        (successful_enabling  != len(differences["enable"])) or \
        (successful_disabling != len(differences["disable"])):
        raise Exception("Script finished with errors. Please check logs")

    logger.info("Script finished")


def handler(event, context):
    """Entrypoint for Lambda event

    :param event:
    :param context:
    :return:
    """
    logger.info("Starting script with following parameters: ")
    logger.info(f"WORKMAIL_ORGANIZATION_ID: {WORKMAIL_ORGANIZATION_ID}")
    logger.info(f"IDENTITYSTORE_ID: {IDENTITYSTORE_ID}")
    logger.info(f"IDENTITY_CENTER_INSTANCE_ARN: {IDENTITY_CENTER_INSTANCE_ARN}")
    logger.info(f"IDENTITY_CENTER_APPLICATION_ARN: {IDENTITY_CENTER_APPLICATION_ARN}")
    logger.info(f"OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL: {OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL}")

    # First of all we're checking environmental variables needed for script
    if not WORKMAIL_ORGANIZATION_ID or \
            not IDENTITYSTORE_ID or \
            not IDENTITY_CENTER_INSTANCE_ARN or \
            not IDENTITY_CENTER_APPLICATION_ARN or \
            not OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL:
        raise Exception("Missing required environment variables")

    main()
