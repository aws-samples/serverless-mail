import subprocess
import json
import re
import os

def run_my_variables_script():
    """Runs my-variables.py and captures the output."""
    try:
        result = subprocess.run(['python3', 'my-variables.py'], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Error executing my-variables.py: {result.stderr}")
        return result.stdout
    except Exception as e:
        raise RuntimeError(f"Execution failed: {str(e)}")

def parse_variables(output):
    """Extracts key-value pairs from my-variables.py output."""
    variables = {}
    for line in output.split('\n'):
        match = re.match(r"(.*?)\s{2,}(.*)", line)
        if match:
            key, value = match.groups()
            variables[key.strip()] = value.strip()
    return variables

def generate_app_py(variables):
    """Creates app.py with variables inserted, asking before overwriting if it exists."""
    template = """import aws_cdk as cdk
import cdk_nag as nag

from OktaIdCWorkMailLambdaExample.stack import LambdaStack

app = cdk.App()
cdk.Aspects.of(app).add(nag.AwsSolutionsChecks(verbose=True))
LambdaStack(
    app,
    "OktaIdCWorkMailLambdaExample",
    env=cdk.Environment(
        account="{account}",
        region="{region}"
    ),
    lambda_environment = {{
        "IDENTITYSTORE_ID": "{identity_store_id}",
        "IDENTITY_CENTER_INSTANCE_ARN": "{identity_center_instance_arn}",
        "IDENTITY_CENTER_APPLICATION_ARN": "{identity_center_application_arn}",
        "WORKMAIL_ORGANIZATION_ID": "{workmail_organization_id}",
        "OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL": "{okta_group_id}",
        "LOG_LEVEL": "INFO",
    }}
)

app.synth()
"""
    formatted_script = template.format(
        account=variables.get("AWS Account ID", ""),
        region=variables.get("AWS Region", ""),
        identity_store_id=variables.get("Identity Store ID", ""),
        identity_center_instance_arn=variables.get("Identity Center Instance ARN", ""),
        identity_center_application_arn=variables.get("Identity Center Application ARN", ""),
        workmail_organization_id=variables.get("WorkMail Organization ID", ""),
        okta_group_id=variables.get("OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL", "workmail_users")
    )
    
    if os.path.exists("app.py"):
        overwrite = input("app.py already exists. Overwrite? (yes/no): ").strip().lower()
        if overwrite not in ["yes", "y"]:
            print("Operation canceled. app.py was not modified.")
            return
    
    with open("app.py", "w") as file:
        file.write(formatted_script)
    print("app.py has been successfully generated.")

if __name__ == "__main__":
    output = run_my_variables_script()
    variables = parse_variables(output)
    generate_app_py(variables)
