import aws_cdk as cdk

from OktaIdCWorkMailLambdaExample.stack import LambdaStack

app = cdk.App()
LambdaStack(
    app,
    "OktaIdCWorkMailLambdaExample",
    env=cdk.Environment(
        account="",
        region=""
    ),
    lambda_environment = {
        "IDENTITY_CENTER_INSTANCE_ARN": "",
        "IDENTITY_CENTER_APPLICATION_ARN": "",
        "WORKMAIL_ORGANIZATION_ID": "",
        "OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL": "",
        "LOG_LEVEL": "INFO",
    }
)

app.synth()
