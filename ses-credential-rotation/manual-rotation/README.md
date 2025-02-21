# Amazon SES Credential Rotation

This folder contains Cloudformation templates and Lambda code that deploys the Manual Amazon SES Credential Rotation solution outlined in [this blog post](https://aws.amazon.com/blogs)

## Deployment

You will require an S3 bucket in the relevant region to store the Lambda code packages required to deploy the solution. This can be created via the console or you can use the AWS CLI

```
aws s3api create-bucket --bucket cloudformation-code-12345
```

Once created, open a terminal in the manual-rotation folder and run the aws cloudformation package command to package the Lambda functions and upload them to S3. This command will output an updated version of the template to the --output-template-file location

```
aws cloudformation package --template-file sesmanualrotation.yaml --s3-bucket cloudformation-code-12345 --output-template-file sesmanualoutput.yaml
```

You can then deploy the template via the AWS Console or using the AWS CLI

```
aws cloudformation deploy --template-file sesmanualoutput.yaml --stack-name SESManualRotation --parameter-overrides SecretName=sessecret IAMUserName=sessecret SESSendingResourceCondition=identity SESSendingResourceValue=myidentity ConfirmationEmailAddress=myteam@mycompany.com  --capabilities CAPABILITY_NAMED_IAM
```

### Parameter Definition

The following parameters are required when deploying the Cloudformation stack

* SecretName - How to name the secret values in Systems Manager Parameter Store, for example "SESEmailSecret"
* IAMUserName - The name of the IAM user to create that will be able to send email, for example "ses-send-email-user"
* KMSKeyID - (Optional) The ID of a Customer Managed key to encrypt the secret in Parameter Store, the default key AWS managed key is used if this is not specified 
* SESSendingResourceCondition - Valid values are configuration-set or identity - This is the resource type that will be given IAM permission to send raw email via SMTP
* SESSendingResourceValue - This is the resource name that will be given IAM permission to send raw email via SMTP. This must be a configuration-set name or identity name, depending on SESSendingResourceCondition
* * If you used configuration-set, the format for value is:  arn:${Partition}:ses:${Region}:${Account}:configuration-set/${ConfigurationSetName}
* * If you used identity, the format for value is: arn:${Partition}:ses:${Region}:${Account}:identity/${IdentityName}     
* ConfirmationEmailAddress - The email address to send the confirmation emails to

## Stack Creation

* AWS CloudFormation will provision and configure the resources as defined in the template. This will take about 10 minutes to fully deploy. You can view the status under the stack’s resources tab in the AWS CloudFormation console.
* As the template is deploying, you will receive an email to the ConfirmationEmailAddress asking you to confirm you wish to subscribe, ensure you click this link to receive further emails from the SNS topic.
* The template deploys an Amazon EventBridge Scheduler to trigger the execution of the Credential Rotation step function. This is initially setup to execute on the last day of every 3rd month (31st Jan, 30th April, 31st July, 31st October). You can adjust this schedule via the Scheduler section of the EventBridge console, the name of the schedule is also listed as an output of the CloudFormation stack.

NOTE - Note, this solution can be deployed multiple times to generate additional users and secrets to support a scenario where you have more than one AWS SES sending requirement, or want to limit the impact of a compromised credential. Each deployment requires a unique IAMUserName and SecretName.

## Operating the solution

The solution reads the list of servers that are using this secret from a DynamoDB table, this will need manually populating in order for the solution to send the necessary alerts. This can be done via the console or via the command line :

```
aws dynamodb put-item --table-name manualrotation-AWSSESRotationDynamoDBTable-133GO9OY7DDID --item "{\"Server\": {\"S\": \"Server1\"}}"
```

## Testing the solution

* In the AWS console, go to CloudFormationStack’s Resources tab
* Find the LogicalID = CredentialRotationLambdaStateMachine
* Click the PhysicalID link to open the Step Function
* Click Start execution & Click Start execution button
* Follow the execution in the graph view or table view

## Remediating a compromised credential

By default, the solution checks every 24 hours to see if the manual rotation emails have been acknowledged. If you need to response to a credential compromise quickly, you can de-activate the compromised credential manually in the IAM user console. When you check the Security Credentials tab of the user you should see two keys, both with details of when they were Created, this information can be used to identify the oldest credential.

# Costs to operate

All AWS services used in this solution have negligible cost, it is likely monthly costs will be well below $1.00 when operating this solution. 




