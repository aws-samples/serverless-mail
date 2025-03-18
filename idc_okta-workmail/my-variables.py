import subprocess
import json

def run_aws_command(command):
    """Runs an AWS CLI command and returns the output as a string, stripping any extra whitespace."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip() or "Error: No data returned"
    except Exception as e:
        return f"Error: {str(e)}"

def get_identity_center_instance():
    """Fetches the Identity Center Instance ARN and Identity Store ID."""
    try:
        command = "aws sso-admin list-instances --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return None, f"Error: {result.stderr.strip()}"

        data = json.loads(result.stdout)
        instances = data.get("Instances", [])

        if not instances:
            return None, "Error: No Identity Center Instances found"

        return instances[0].get("InstanceArn"), instances[0].get("IdentityStoreId")

    except json.JSONDecodeError:
        return None, "Error: Unable to parse JSON response"
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_identity_center_application_arn(instance_arn):
    """Fetches the first available Identity Center Application ARN."""
    if not instance_arn or "Error" in instance_arn:
        return "Error: Invalid or missing Identity Center Instance ARN"

    try:
        command = f"aws sso-admin list-applications --instance-arn {instance_arn} --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        data = json.loads(result.stdout)
        applications = data.get("Applications", [])

        return applications[0].get("ApplicationArn", "Application ARN not found") if applications else "No applications found"

    except json.JSONDecodeError:
        return "Error: Unable to parse JSON response"
    except Exception as e:
        return f"Error: {str(e)}"

def get_idc_group_id(identity_store_id, group_name="workmail_users"):
    """Fetches the Group ID of a specified IAM Identity Center (IdC) group by name."""
    if not identity_store_id or "Error" in identity_store_id:
        return "Error: Invalid or missing Identity Store ID"

    try:
        command = f"aws identitystore list-groups --identity-store-id {identity_store_id} --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        data = json.loads(result.stdout)
        groups = data.get("Groups", [])

        for group in groups:
            if group.get("DisplayName") == group_name:
                return group.get("GroupId", "Error: Group ID not found")

        return f"Error: Group '{group_name}' not found"

    except json.JSONDecodeError:
        return "Error: Unable to parse JSON response"
    except Exception as e:
        return f"Error: {str(e)}"

def get_active_workmail_organization_id():
    """Fetches the WorkMail Organization ID for the first active organization."""
    try:
        command = "aws workmail list-organizations --output json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"

        data = json.loads(result.stdout)
        organizations = data.get("OrganizationSummaries", [])

        for org in organizations:
            if org.get("State", "").lower() == "active":
                return org.get("OrganizationId", "Error: Organization ID not found")

        return "Error: No active WorkMail organization found"

    except json.JSONDecodeError:
        return "Error: Unable to parse JSON response"
    except Exception as e:
        return f"Error: {str(e)}"

# Fetch general AWS configuration details
commands = {
    "AWS Account ID": "aws sts get-caller-identity --query 'Account' --output text",
    "AWS Region": "aws configure get region",
}

aws_values = {key: run_aws_command(cmd) for key, cmd in commands.items()}

# Fetch Identity Center Instance ARN and Identity Store ID
identity_center_instance_arn, identity_store_id = get_identity_center_instance()
aws_values["Identity Center Instance ARN"] = identity_center_instance_arn
aws_values["Identity Store ID"] = identity_store_id

# Fetch Identity Center Application ARN
aws_values["Identity Center Application ARN"] = get_identity_center_application_arn(identity_center_instance_arn)

# Fetch IAM Identity Center Group ID
aws_values["OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL"] = get_idc_group_id(identity_store_id, "workmail_users")

# Fetch Active WorkMail Organization ID
aws_values["WorkMail Organization ID"] = get_active_workmail_organization_id()

# Print formatted output
print("\n======================================")
print("         AWS Configuration            ")
print("======================================")

for key, value in aws_values.items():
    print(f"{key.ljust(40)} {value}")

print("======================================\n")
