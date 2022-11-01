#!/usr/bin/env python3

from aws_cdk import App, Aspects, Environment
from cdk_nag import AwsSolutionsChecks, NagSuppressions

import CONFIG
from email_security.email_security_stack import EmailSecurityStack
from email_security.aspects import DmarcChecker

app = App()

email_security_stack = EmailSecurityStack(
    app,
    "EmailSecurityStack",
    env=Environment(account=CONFIG.ACCOUNT, region=CONFIG.REGION),
)

# Validate DMARC record
Aspects.of(email_security_stack).add(DmarcChecker())

# Best practice checks
Aspects.of(email_security_stack).add(AwsSolutionsChecks())

NagSuppressions.add_resource_suppressions(
    construct=email_security_stack,
    apply_to_children=True,
    suppressions=[
        {
            "id": "AwsSolutions-IAM4",
            "reason": "CDK custom resources use AWS managed policies",
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "CDK custom resources use wildcard permissions",
        },
    ],
)

app.synth()
