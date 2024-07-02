# Amazon SES Credential Rotation

This folder contains Cloudformation templates and Lambda code that deploys the Automatic Amazon SES Credential Rotation solution outlined in [this blog post](https://aws.amazon.com/blogs)

## Deployment

You will require an S3 bucket in the relevant region to store the Lambda code packages required to deploy the solution. This can be created via the console or you can use the AWS CLI

```
aws s3api create-bucket --bucket cloudformation-code-12345
```

Once created, open a terminal in the automatic-rotation folder and run the aws cloudformation package command to package the Lambda functions and upload them to S3. This command will output an updated version of the template to the --output-template-file location

```
aws cloudformation package --template-file sesautomaticrotation.yaml --s3-bucket cloudformation-code-12345 --output-template-file sesautomaticoutput.yaml
```

You can then deploy the template via the AWS Console or using the AWS CLI

```
aws cloudformation deploy --template-file sesautomaticoutput.yaml --stack-name SESAutomaticlRotation --parameter-overrides SecretName=sessecret IAMUserName=sessecret SESSendingResourceCondition=identity SESSendingResourceValue=myidentity SSMRotationDocument=MySSMDocument SSMServerTag=EmailServers SSMServerTagValue=True --capabilities CAPABILITY_NAMED_IAM
```

### Parameter Definition

The following parameters are required when deploying the Cloudformation stack

* SecretName - How to name the secret values in Systems Manager Paramter Store, for example "SESEmailSecret"
* IAMUserName - The name of the IAM user to create that will be able to send email, for example "ses-send-email-user"
* MaximumSecretAgeInDays - The maximum age of a secret, after this it will be rotated
* KMSKeyID - (Optional) The ID of a Customer Managed key to encrypt the secret in Secrets Manager, the default key AWS managed key is used if this is not specified. 
* SESSendingResourceCondition - Valid values are configuration-set or identity - This is the resource type that will be given IAM permission to send raw email via SMTP
* SESSendingResourceValue - This is the resource name that will be given IAM permission to send raw email via SMTP. This must be a configuration-set name or identity name, depending on SESSendingResourceCondition
* * If you used configuration-set, the format for value is:  arn:${Partition}:ses:${Region}:${Account}:configuration-set/${ConfigurationSetName}
* * If you used identity, the format for value is: arn:${Partition}:ses:${Region}:${Account}:identity/${IdentityName}
* SSMRotationDocument - The name of the SSM document to use to rotate the password on the relevant servers
* SSMServerTag - The name of the Tag to identify which server to run the SSM Rotation Document On
* SSMServerTagValue - The value of the Tag to identify which servers to run the 

## Stack Creation

* AWS CloudFormation will provision and configure the resources as defined in the template. This will take about 10 minutes to fully deploy. You can view the status under the stack’s resources tab in the AWS CloudFormation console.
* The template enables automatic secret rotation for the secret based on the MaximumSecretAgeInDays, the exact rotation schedule will be managed by AWS Secrets Manager

NOTE - Note, this solution can be deployed multiple times to generate additional users and secrets to support a scenario where you have more than one AWS SES sending requirement, or want to limit the impact of a compromised credential. Each deployment requires a unique IAMUserName and SecretName.

## Using your own KMS Key

If you make use of your own KMS Key, the Key policy of the Customer Managed Key must allow the IAM role of the Rotation Lambda to perform kms:Decrypt and kms:GenerateDataKey actions. As this role is not created until after the template is deployed just must use the "Rotate Secret Immediately" button to create the first secret once the role has been given the neccessary permission to use the KMS key, until that time the Secret will appear as empty in AWS Secrets Manager

## Testing the solution

To test the solution, you can request that Secrets Manager performs an immediate rotation. Locate the secret in Secrets Manager and then select "Rotate Secret immediately" from the Rotation tab of the Console.

You can track the progress of the rotation by locating the logs of the Lambda that is deployed to manage the rotation. 

* In the AWS console, go to CloudFormationStack’s Resources tab
* Find the LogicalID = SESSecretRotationFunction
* Click the PhisicalID link to open the Lambda
* Under the Monitor Tab, select the "View CloudWatch logs" button in the to right
* The logs should show the rotation flow through 4 stages - create_secret, set_secret, test_secret, finish_secret. More details of each stage are available [here](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html)

## Remediating a compromised credential

A compromised credential can be remediated using the "Rotate Secret Immediately" button under the Rotation tab in the Secrets Manager Console, this will execute an identical process to a normal rotation

# Costs to operate

All AWS services used in this solution have negligible cost, it is likely monthly costs will be well below $1.00 when operating this solution. 




