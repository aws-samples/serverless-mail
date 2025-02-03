from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    BundlingOptions,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
)
from aws_cdk.aws_iam import PolicyDocument
from constructs import Construct


class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, lambda_environment: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create IAM role for Lambda
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRoleForIdCWorkMailSync",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "IdcWorkMailUserSyncPolicy": PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            sid="AllowToCreateWorkmailUsers",
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "workmail:CreateUser",
                                "workmail:ListUsers",
                                "workmail:RegisterToWorkMail",
                                "workmail:DeregisterFromWorkMail",
                                "workmail:DescribeOrganization",
                                "workmail:DescribeIdentityProviderConfiguration",
                            ],
                            resources=[
                                f"arn:aws:workmail:{self.region}:{self.account}:organization/{lambda_environment['WORKMAIL_ORGANIZATION_ID']}",
                            ]
                        ),
                        iam.PolicyStatement(
                            sid="AllowSESActions",
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ses:GetIdentityVerificationAttributes", # is needed for RegisterToWorkMail API
                            ],
                            resources=[
                                "*",
                            ]
                        ),
                        iam.PolicyStatement(
                            sid="AllowToListIdentitystoreUsers",
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "identitystore:DescribeUser",
                                "identitystore:ListGroupMemberships"
                            ],
                            resources=[
                                "*",
                            ]
                        ),
                        iam.PolicyStatement(
                            sid="AllowIdCInstanceOperations",
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sso:DescribeInstance",
                            ],
                            resources=[
                                lambda_environment['IDENTITY_CENTER_INSTANCE_ARN'],
                            ]
                        ),
                        iam.PolicyStatement(
                            sid="AllowIdCApplicationsOperations",
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sso:CreateApplicationAssignment",
                            ],
                            resources=[
                                lambda_environment['IDENTITY_CENTER_APPLICATION_ARN'],
                            ]
                        ),
                        iam.PolicyStatement(
                            sid="AllowCloudwatchOperations",
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*",
                                f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*:log-stream:*"
                            ]
                        )
                    ]
                ),
            }
        )

        # Create Log Group with retention
        log_group = logs.LogGroup(
            self,
            "ScheduledLambdaSyncrhonizerLogGroup",
            log_group_name=f"/aws/lambda/{construct_id}",
            retention=logs.RetentionDays.ONE_WEEK,  # Adjust retention period as needed
            removal_policy=RemovalPolicy.DESTROY  # Optional: auto-delete when stack is destroyed
        )

        dependencies_layer = _lambda.LayerVersion(
            self,
            "DependenciesLayer",
            code=_lambda.Code.from_asset(
                "OktaIdCWorkMailLambdaExample/lambda",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output/python && cp -au . /asset-output/python"
                    ],
                )
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
        )

        # Create Lambda function with the role
        lambda_function = _lambda.Function(
            self,
            "ScheduledLambdaSyncrhonizer",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.handler",
            code=_lambda.Code.from_asset(
                "OktaIdCWorkMailLambdaExample/lambda",
            ),
            layers=[dependencies_layer],
            timeout=Duration.minutes(10),
            memory_size=128,
            role=lambda_role,
            environment={
                **lambda_environment,
            },
            log_group=log_group,
        )

        # Create CloudWatch Event Rule
        rule = events.Rule(
            self,
            "ScheduleRule",
            schedule=events.Schedule.rate(Duration.minutes(15)),
            enabled=True,
        )

        # Add Lambda function as target
        rule.add_target(targets.LambdaFunction(lambda_function))
