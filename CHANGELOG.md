# Changelog

## 2025-07-27

### Security Fixes (Holmes CSR Scan)

- **Credential exposure**: Removed `logger.info(event)` and `print(event)` calls that logged sensitive data (SecretAccessKey, passwords, task tokens) in Lambda handlers across `ses-credential-rotation/` and `lambda-email-parser/`
- **PII in public code**: Replaced real AWS internal usernames (`evaleah-Isengard`, `jhblee-Isengard`) with placeholder values in `vdm-to-rds/cloudformation/qsres.yaml`
- **Security groups**: Removed 0.0.0.0/0 all-traffic, SSH, and HTTPS ingress rules from `RDSSecurityGroup` in `vdm-to-rds/cloudformation/cf_vdmtoqsdata.yaml`
- **Command injection**: Converted all `subprocess.run(command, shell=True)` to list-based execution in `idc_okta-workmail/my-variables.py`
- **SQL injection**: Added input validation (regex allowlist) for table names and dates in `vdm-to-rds/metricstoMySQL.py`
- **RDS encryption**: Added `StorageEncrypted: true` to DB instance in `vdm-to-rds/cloudformation/cf_vdmtoqsdata.yaml`
- **KMS key rotation**: Enabled `enable_key_rotation=True` on both KMS keys in `serverless-iot-email-attachment-processing/stack.py`
- **IAM least privilege**: Scoped `iam:CreateAccessKey`/`iam:DeleteAccessKey` from wildcard `*` to `!GetAtt SESIAMUser.Arn` in `ses-credential-rotation/manual-rotation/sesmanualrotation.yaml`
- **QuickSight DisableSsl**: Removed unnecessary `DisableSsl: false` property from data sources in `vdm-to-rds/cloudformation/qsres.yaml`
- **Disclaimer wording**: Updated production-readiness disclaimer in `idc_okta-workmail/README.md`

### Added

- `.holmesignore` to exclude vendored third-party libraries (pymysql, xmltodict, crhelper) from security scans
- Production considerations section in `ses-credential-rotation/README.md` covering DynamoDB encryption, SNS encryption, S3 versioning, IAM least privilege, API Gateway auth, and PITR
- Inline `holmes-ignore` comments for intentional sample-code patterns (DynamoDB SSE, SNS encryption, `logs:*` wildcards, S3 versioning/logging)

## 2025-07-24

### Updated

- **ses-credential-rotation/automatic-rotation**: Upgraded Lambda runtime from Python 3.10 to Python 3.12
- **ses-credential-rotation/manual-rotation**: Upgraded Lambda runtime from Python 3.10 to Python 3.12 (all 5 functions)
- **vdm-to-rds/cloudformation**: Upgraded Lambda runtime from Python 3.9 to Python 3.12 (`downloadvdmqsfiles`, `createsesvdmtables`)

### Rationale

Python 3.9 reached end-of-life in October 2025. Python 3.10 reaches end-of-life in October 2026. Upgrading to Python 3.12 (EOL October 2028) ensures continued security patches and AWS Lambda runtime support.
