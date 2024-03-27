import aws_cdk.aws_cloudwatch_actions as cw_actions
import re
from aws_cdk import Aws, CfnOutput, CfnParameter, Duration, RemovalPolicy, Size, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_lambda_event_sources as lambda_notifications
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3_notifications
from aws_cdk import aws_ses as ses
from aws_cdk import aws_ses_actions as ses_actions
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sqs as sqs
from constructs import Construct

EMAIL_REGEX = r'\b^[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+$\b'
CONFIG_SET_NAME_REGEX = r'\b^[a-zA-Z0-9-]+$\b'


# main stack for the SES solution
class SesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sender_email = self.node.try_get_context("SenderEmail")
        recipient_email = self.node.try_get_context("RecipientEmail")
        configuration_set_name = self.node.try_get_context("ConfigurationSetName")

        # Validate configuration set name
        if not configuration_set_name or not re.fullmatch(CONFIG_SET_NAME_REGEX, configuration_set_name):
            raise ValueError(f"Please provide configuration set name. The provided value is {configuration_set_name}")

        # Ensure the sender and recipient email address CDK input parameters are neither empty nor ill-formatted
        if not sender_email or not re.fullmatch(EMAIL_REGEX, sender_email):
            raise ValueError(f"Please provide sender email address. The provided sender value is {sender_email}")

        if not recipient_email or not re.fullmatch(EMAIL_REGEX, recipient_email):
            raise ValueError(f"Please provide recipient email address. The provided sender value is {recipient_email}")

        sns_key = kms.Key(self, "sns-topic-key", alias="sns-key", )
        logs_key = kms.Key(self, "log-key")

        # Grant CloudWatch access to the KMS keys
        sns_key.add_to_resource_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.ServicePrincipal("cloudwatch.amazonaws.com")],
            actions=[
                "kms:GenerateDataKey*",
                "kms:Decrypt",
                "kms:DescribeKey",
            ],
            resources=["*"]
        ))
        logs_key.add_to_resource_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.ServicePrincipal("logs.amazonaws.com")],
            actions=[
                "kms:GenerateDataKey*",
                "kms:Encrypt*",
                "kms:Decrypt*",
                "kms:ReEncrypt*",
                "kms:GenerateDataKey*",
                "kms:Describe*"
            ],
            resources=["*"]
        ))

        fallback_subscribers_topic = sns.Topic(
            self, "fallback-subscribers", master_key=sns_key
        )

        notifications_topic = sns.Topic(self, "notifications", master_key=sns_key)

        # deny publishing to topic if not over SSL
        fallback_subscribers_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.ServicePrincipal("ses.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[fallback_subscribers_topic.topic_arn],
                conditions={
                    "Bool": {"aws:SecureTransport": "false"},
                },
            )
        )

        notifications_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.ServicePrincipal("ses.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[notifications_topic.topic_arn],
                conditions={
                    "Bool": {"aws:SecureTransport": "false"},
                },
            )
        )

        notifications_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("cloudwatch.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[notifications_topic.topic_arn],
            )
        )

        incoming_prefix = "incoming"

        incoming_queue_dlq = sqs.Queue(
            self,
            f"{incoming_prefix}-sqs-dlq",
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            enforce_ssl=True,
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(30),
        )

        incoming_queue = sqs.Queue(
            self,
            f"{incoming_prefix}-sqs",
            enforce_ssl=True,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            retention_period=Duration.minutes(15),
            visibility_timeout=Duration.seconds(30),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=1, queue=incoming_queue_dlq
            ),
        )

        # Setup SQS Alarms

        incoming_queue.metric_approximate_age_of_oldest_message(
            period=Duration.minutes(2)
        ).create_alarm(
            self, "old-messages-alarm", evaluation_periods=1, threshold=180
        ).add_alarm_action(
            cw_actions.SnsAction(notifications_topic)
        )

        incoming_queue.metric_number_of_messages_received(
            period=Duration.minutes(5)
        ).create_alarm(
            self, "incoming-messages-spike", evaluation_periods=1, threshold=180
        ).add_alarm_action(
            cw_actions.SnsAction(notifications_topic)
        )

        incoming_queue_dlq.metric_approximate_number_of_messages_visible(
            period=Duration.minutes(2)
        ).create_alarm(
            self, "failing-messages-in-dlq", evaluation_periods=1, threshold=50
        ).add_alarm_action(
            cw_actions.SnsAction(notifications_topic)
        )

        lifecycle_rule = s3.LifecycleRule(
            id="delete-after-expiry",
            abort_incomplete_multipart_upload_after=Duration.days(1),
            enabled=True,
            noncurrent_version_expiration=Duration.days(1),
            expiration=Duration.days(14),
        )

        incoming_bucket = s3.Bucket(
            self,
            "incoming",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[lifecycle_rule],
            enforce_ssl=True,
        )

        attachments_bucket = s3.Bucket(
            self,
            "attachments",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[lifecycle_rule],
            enforce_ssl=True,
        )

        # enforce bucket access over SSL
        incoming_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[
                    f"{incoming_bucket.bucket_arn}/*",
                    f"{incoming_bucket.bucket_arn}",
                ],
                conditions={
                    "Bool": {"aws:SecureTransport": "false"},
                },
            )
        )

        incoming_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("ses.amazonaws.com")],
                actions=["s3:PutObject"],
                resources=[f"{incoming_bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {"AWS:SourceAccount": Aws.ACCOUNT_ID},
                    "StringLike": {"Aws:SourceArn": "arn:aws:ses:*"},
                },
            )
        )

        rule_set = ses.ReceiptRuleSet(self, "rule-set")

        ses.ReceiptRule(
            self,
            "s3-rule",
            enabled=True,
            rule_set=rule_set,
            scan_enabled=True,
            tls_policy=ses.TlsPolicy.REQUIRE,
            actions=[
                ses_actions.S3(
                    bucket=incoming_bucket, object_key_prefix=f"{incoming_prefix}/"
                )
            ],
            recipients=[recipient_email],
        )

        log_group = logs.LogGroup(
            self,
            "attachment-processor-log-group",
            removal_policy=RemovalPolicy.DESTROY,
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=logs_key
        )

        attachment_processor_role = iam.Role(
            scope=self,
            id="attachment-processor-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        attachment_processor = _lambda.Function(
            scope=self,
            id="attachment-processor",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset("./lambdas/attachment_processor"),
            role=attachment_processor_role,
            environment={
                "ATTACHMENTS_BUCKET": attachments_bucket.bucket_name,
                "EMAIL_REGEX_CODE": ":Email_Rxers_Code:",
                "INCOMING_BUCKET": incoming_bucket.bucket_name,
                "LOG_LEVEL": "INFO",
                "POWERTOOLS_SERVICE_NAME": "attachment-processor",
                "PRESIGNED_EXPIRATION": str(36 * 60 * 60),  # 36 hours in seconds
                "SENDER_EMAIL": sender_email,
                "SNS_TOPIC": fallback_subscribers_topic.topic_arn,
            },
            timeout=Duration.seconds(15),
            memory_size=240,
            ephemeral_storage_size=Size.mebibytes(5000),
            log_group=log_group,
            log_format="JSON",
            architecture=_lambda.Architecture.ARM_64,
            layers=[
                _lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "powertools-layer",
                    # Official AWS powertools layer per https://awslabs.github.io/aws-lambda-powertools-python/2.10.0/
                    f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:47",
                )
            ],
        )

        attachment_processor.node.add_dependency(log_group)

        attachment_processor.add_to_role_policy(
            statement=iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ses:SendRawEmail"],
                resources=[
                    f"arn:aws:ses:{self.region}:{Aws.ACCOUNT_ID}:configuration-set/{configuration_set_name}",
                    f"arn:aws:ses:{self.region}:{Aws.ACCOUNT_ID}:identity/{sender_email}",
                ],
                conditions={
                    "StringEquals": {
                        "ses:FromAddress": sender_email
                    }
                }
            )
        )

        log_group.grant_write(attachment_processor)

        # push created object notifications onto incoming SQS queue
        incoming_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, s3_notifications.SqsDestination(incoming_queue)
        )

        # consume incoming events from SQS queue
        attachment_processor.add_event_source(
            lambda_notifications.SqsEventSource(
                queue=incoming_queue,
                max_concurrency=2,
                batch_size=1,
            )
        )

        incoming_bucket.grant_read(attachment_processor)
        attachments_bucket.grant_read_write(attachment_processor)
        fallback_subscribers_topic.grant_publish(attachment_processor)

        CfnOutput(
            self, "FallbackTopicName", value=fallback_subscribers_topic.topic_name
        )
        CfnOutput(self, "FallbackTopicArn", value=fallback_subscribers_topic.topic_arn)
        CfnOutput(self, "IncomingBucketName", value=incoming_bucket.bucket_name)
        CfnOutput(self, "AttachmentsBucketName", value=attachments_bucket.bucket_name)
