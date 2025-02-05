import aws_cdk as cdk
import cdk_nag as nag

from OktaIdCWorkMailLambdaExample.stack import LambdaStack

app = cdk.App()
cdk.Aspects.of(app).add(nag.AwsSolutionsChecks(verbose=True))
LambdaStack(
    app,
    "OktaIdCWorkMailLambdaExample",
    env=cdk.Environment(
        account="",
        region=""
    ),
    lambda_environment = {
        "IDENTITYSTORE_ID": "",
        "IDENTITY_CENTER_INSTANCE_ARN": "",
        "IDENTITY_CENTER_APPLICATION_ARN": "",
        "WORKMAIL_ORGANIZATION_ID": "",
        "OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL": "",
        "LOG_LEVEL": "INFO",
    }
)

app.synth()
