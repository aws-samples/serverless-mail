# Amazon SES Credential Rotation

This folder contains Cloudformation templates and Lambda code that deploys the Amazon SES Credential Rotation solutions outlined in [this blog post](https://aws.amazon.com/blogs)

Depending on your use case, there are two solutions, for deployment instructions please check out the individual Readme files :

* [automatic-rotation](automatic-rotation/README.md)
* [manual-rotation](manual-rotation/README.md)

## Production Considerations

This code is provided as sample/demo code. Before deploying in a production environment, consider implementing the following:

- **DynamoDB Encryption**: Enable server-side encryption (SSE) with a KMS Customer Managed Key (CMK) on the `AWSSESRotationDynamoDBTable` to encrypt data at rest. Add `SSESpecification` with `SSEEnabled: true` and `SSEType: KMS` along with a `KMSMasterKeyId`.
- **SNS Topic Encryption**: Add KMS encryption to the `ConfirmationEmailSNSTopic` by setting the `KmsMasterKeyId` property to ensure notification data is encrypted at rest.
- **S3 Bucket Versioning and Access Logging**: Enable versioning and server access logging on all S3 buckets to support audit trails and data recovery.
- **IAM Least Privilege**: Review all IAM policies and scope resource ARNs and actions to the minimum required for your workload. Replace wildcard actions (e.g., `logs:*`) with specific actions such as `logs:CreateLogGroup`, `logs:CreateLogStream`, and `logs:PutLogEvents`.
- **API Gateway Authentication**: Add authentication (IAM, Cognito, or Lambda authorizer) to the API Gateway callback endpoint if exposed to the internet.
- **DynamoDB Point-in-Time Recovery**: Enable point-in-time recovery (PITR) on DynamoDB tables to protect against accidental data loss.
