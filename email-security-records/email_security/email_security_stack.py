from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cf_origins,
    aws_iam as iam,
    aws_route53 as route53,
    aws_route53_targets as route_53_targets,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
)
from cdk_nag import NagSuppressions
from constructs import Construct

import CONFIG

BIMI_DOMAIN = f"{CONFIG.BIMI_ASSETS_SUBDOMAIN}.{CONFIG.EMAIL_DOMAIN}"
MTA_STS_DOMAIN = f"mta-sts.{CONFIG.EMAIL_DOMAIN}"


class EmailSecurityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if CONFIG.ROUTE_53_HOSTED:

            # Import hosted zone
            dns_zone = route53.HostedZone.from_lookup(
                self, "dns_zone", domain_name=CONFIG.EMAIL_DOMAIN
            )

            # Generate ACM certificate
            bimi_tls_cert = acm.DnsValidatedCertificate(
                self,
                "tls_cert",
                hosted_zone=dns_zone,
                domain_name=BIMI_DOMAIN,
                subject_alternative_names=[MTA_STS_DOMAIN],
                region="us-east-1",
            )
            NagSuppressions.add_resource_suppressions(
                construct=bimi_tls_cert,
                apply_to_children=True,
                suppressions=[
                    {
                        "id": "AwsSolutions-L1",
                        "reason": "The custom resource Lambda does not use the latest runtime",
                    },
                ],
            )

        else:

            # Import certificate from ACM
            bimi_tls_cert = acm.Certificate.from_certificate_arn(
                self, "tls_cert", certificate_arn=CONFIG.TLS_CERTIFICATE_ARN
            )

        ##### S3

        log_bucket = s3.Bucket(
            self,
            "bimi_log_bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                {
                    "expiration": Duration.days(CONFIG.LOG_RETENTION_DAYS)
                }
            ]
        )
        log_bucket.grant_write(iam.ServicePrincipal("delivery.logs.amazonaws.com"))
        NagSuppressions.add_resource_suppressions(
            construct=log_bucket,
            suppressions=[
                {
                    "id": "AwsSolutions-S1",
                    "reason": "Access logging is not enabled on the log bucket",
                }
            ],
        )

        asset_bucket = s3.Bucket(
            self,
            "bimi_bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True,
            server_access_logs_bucket=log_bucket,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # MTA-STS policy document

        deployment = s3_deployment.BucketDeployment(
            self,
            "bimi_assets",
            destination_bucket=asset_bucket,
            sources=[s3_deployment.Source.asset(path="assets")],
        )

        ##### CloudFront

        oai = cloudfront.OriginAccessIdentity(self, "bimi_oai")
        asset_bucket.grant_read(identity=oai)

        distribution = cloudfront.Distribution(
            self,
            "bimi_distribution",
            domain_names=[BIMI_DOMAIN, MTA_STS_DOMAIN],
            certificate=bimi_tls_cert,
            default_behavior=cloudfront.BehaviorOptions(
                origin=cf_origins.S3Origin(
                    bucket=asset_bucket, origin_access_identity=oai
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
            ),
            log_bucket=log_bucket,
        )
        NagSuppressions.add_resource_suppressions(
            construct=distribution,
            suppressions=[
                {
                    "id": "AwsSolutions-CFR1",
                    "reason": "Geo restrictions are not required",
                },
                {
                    "id": "AwsSolutions-CFR2",
                    "reason": "WAF is not required",
                },
            ],
        )

        ##### DNS records

        bimi_txt_location = f"default._bimi.{CONFIG.EMAIL_DOMAIN}"
        bimi_txt_value = f"v=BIMI1; l=https://{BIMI_DOMAIN}/{CONFIG.LOGO_FILENAME}"
        if CONFIG.VMC_FILENAME is not None:
            bimi_txt_value += f"; a=https://{BIMI_DOMAIN}/{CONFIG.VMC_FILENAME}"

        mta_sts_txt_location = f"_mta-sts.{CONFIG.EMAIL_DOMAIN}"
        mta_sts_txt_value = f"v=STSv1; id={CONFIG.MTA_STS_ID}"

        tls_rpt_txt_location = f"_smtp._tls.{CONFIG.EMAIL_DOMAIN}"
        tls_rpt_txt_value = f"v=TLSRPTv1; rua={','.join([f'mailto:{address}' for address in CONFIG.TLSRPT_ADDRESSES])}"

        if CONFIG.ROUTE_53_HOSTED:

            # A records

            bimi_subdomain = route53.ARecord(
                self,
                "bimi_subdomain",
                zone=dns_zone,
                record_name=BIMI_DOMAIN,
                target=route53.RecordTarget.from_alias(
                    alias_target=route_53_targets.CloudFrontTarget(
                        distribution=distribution
                    )
                ),
            )

            mta_sts_subdomain = route53.ARecord(
                self,
                "mta_sts_subdomain",
                zone=dns_zone,
                record_name=MTA_STS_DOMAIN,
                target=route53.RecordTarget.from_alias(
                    alias_target=route_53_targets.CloudFrontTarget(
                        distribution=distribution
                    )
                ),
            )

            # TXT records

            bimi_record = route53.TxtRecord(
                self,
                "bimi_record",
                zone=dns_zone,
                comment="BIMI record for email logo display",
                record_name=bimi_txt_location,
                values=[bimi_txt_value],
            )

            mta_sts_record = route53.TxtRecord(
                self,
                "mts_sts_record",
                zone=dns_zone,
                comment="MTA-STS record for mail delivery over TLS",
                record_name=mta_sts_txt_location,
                values=[mta_sts_txt_value],
            )

            tls_rpt_record = route53.TxtRecord(
                self,
                "tlsrpt_record",
                zone=dns_zone,
                comment="TLSRPT record for TLS report delivery",
                record_name=tls_rpt_txt_location,
                values=[tls_rpt_txt_value],
            )

        else:

            bimi_cname = CfnOutput(
                self,
                "bimi_cname",
                value=f"{BIMI_DOMAIN} IN CNAME {distribution.domain_name}",
            )

            mta_sts_cname = CfnOutput(
                self,
                "mta_sts_cname",
                value=f"{MTA_STS_DOMAIN} IN CNAME {distribution.domain_name}",
            )

            bimi_txt = CfnOutput(
                self, "bimi_txt", value=f'{bimi_txt_location}. TXT "{bimi_txt_value}"'
            )

            mta_sts_txt = CfnOutput(
                self,
                "mta_sts_txt",
                value=f'{mta_sts_txt_location}. TXT "{mta_sts_txt_value}"',
            )

            tls_rpt_txt = CfnOutput(
                self,
                "tls_rpt_txt",
                value=f'{tls_rpt_txt_location}. TXT "{tls_rpt_txt_value}"',
            )
