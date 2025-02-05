import subprocess
import json

def run_aws_command(command):
    """Runs an AWS CLI command and returns the output as a string."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        return output if result.returncode == 0 and output else "Not Found"
    except Exception as e:
        return f"Error: {str(e)}"

def get_identity_store_id():
    """Fetch Identity Store ID from AWS SSO Admin."""
    try:
        result = subprocess.run(
            ["aws", "sso-admin", "list-instances", "--query", "Instances[0].IdentityStoreId", "--output", "text"],
            capture_output=True,
            text=True,
            check=True
        )

        identity_store_id = result.stdout.strip().split("\n")[0]

        if not identity_store_id.startswith("d-") or "None" in identity_store_id:
            return "Identity Store ID Not Found"

        return identity_store_id
    except subprocess.CalledProcessError:
        return "Identity Store ID Not Found"

def get_group_id(identity_store_id, region):
    """Fetch the first group ID from AWS Identity Store."""
    try:
        if identity_store_id == "Identity Store ID Not Found":
            return "Identity Store ID Not Found"

        result = subprocess.run(
            ["aws", "identitystore", "list-groups", "--identity-store-id", identity_store_id, "--region", region],
            capture_output=True,
            text=True,
            check=True
        )

        groups = json.loads(result.stdout).get("Groups", [])
        
        if not groups:
            return "No groups found"

        return groups[0]["GroupId"]
    except subprocess.CalledProcessError:
        return "Error retrieving groups"

# Get AWS Account ID
aws_account_id = run_aws_command("aws sts get-caller-identity --query 'Account' --output text")

# Get AWS Region
aws_region = run_aws_command("aws configure get region")
if aws_region == "Not Found":
    aws_region = "us-east-1"
    run_aws_command(f"aws configure set region {aws_region}")

# Get Identity Center Instance ARN
identity_center_instance_arn = run_aws_command(f"aws sso-admin list-instances --region {aws_region} --query 'Instances[0].InstanceArn' --output text")

# Get Identity Store ID
identity_store_id = get_identity_store_id()

# Get WorkMail Organization ID
workmail_org_id = run_aws_command(f"aws workmail list-organizations --region {aws_region} --query 'OrganizationSummaries[0].OrganizationId' --output text")

# Get Identity Center Group ID
idc_group_id = get_group_id(identity_store_id, aws_region)

# Print the results in a structured format
print("\n--------------------------------------")
print(" AWS Environment Information")
print("--------------------------------------")
print(f"AWS Account ID:           {aws_account_id}")
print(f"AWS Region:               {aws_region}")
print(f"Identity Center Instance ARN: {identity_center_instance_arn}")
print(f"Identity Store ID:        {identity_store_id}")
print(f"WorkMail Organization ID: {workmail_org_id}")
print(f"Identity Center Group ID: {idc_group_id}")
print("--------------------------------------\n")
