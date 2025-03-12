# Amazon SES Credential Rotation

This folder contains Cloudformation templates and Lambda code that deploys the Automatic Amazon SES Credential Rotation solution outlined in [this blog post]([https://aws.amazon.com/blogs](https://aws.amazon.com/blogs/messaging-and-targeting/automate-the-creation-rotation-of-amazon-simple-email-service-smtp-credentials/))

## Deployment

If using an IDE, ensure you are using the correct AWS Account credentials. If using AWS CloudShell, ensure you are in the correct AWS region. Ensure you run these commands from the directory that contains this README file

You will need an AWS S3 bucket in the same region as your AWS Systems and Secrets Manager to store the CloudFormation Template and Lambda code packages required to deploy the solution. Copy the following code, replace the value in the <replace-me-with-your-value> and execute in the AWS CLI (optionally you can use the AWS S3 Console). 

- For example your edited code will look like this: 
```aws s3api create-bucket --bucket foo-co-smtp-auto-rotate-092024```

```
aws s3api create-bucket --bucket <provide-a-globally-unique-S3bucket-name> --region <your-aws-region> --create-bucket-configuration '{"LocationConstraint":"<your-aws-region>"}'
```

Note - if you are using a region other than us-east-1, append the create-bucket command with  ```--region us-west-2 --create-bucket-configuration '{"LocationConstraint":"your-aws-region"}'```

Once you've created the S3 bucket, in your terminal app, navigate to /automatic-rotation/, copy & edit the code below, replacing the value in the --s3-bucket <globally-unique-bucket-name-from-above> with the S3 bucket you created in the pervious step. Execute the edited AWS cloudformation package command in the CLI to package the Lambda functions and upload them to S3. This command will output an updated version of the template to the --output-template-file location

For example your edited code will look like this: 
```aws cloudformation package --template-file sesautomaticrotation.yaml --s3-bucket foo-co-smtp-auto-rotate-092024 --output-template-file sesautomaticoutput.yaml```

```
aws cloudformation package --template-file sesautomaticrotation.yaml --s3-bucket <globally-unique-S3bucket-name-from-above> --output-template-file sesautomaticoutput.yaml
```

Copy & edit the code below, replacing the parameters with the correct values for your environment as per the following defintion :

* **SecretName** - Name for the secret values (SMTP passwords) in Systems Manager Parameter Store, for our example we use **sessecret** 
* **IAMUserName** - The name of the IAM user you'll create to send email, for our example we use **sesecret**
* **MaximumSecretAgeInDays** - The maximum age of a secret, after which it is rotated - if not specificed this defaults to **30**
* **KMSKeyID** - (Optional) The ID of a Customer Managed Key to encrypt the secret in Secrets Manager. The default key AWS managed key is used if a Customer Managed Key is not specified. 
* **SESSendingResourceCondition** - Valid values are configuration-set or identity - This is the resource type that will be given IAM permission to send raw email via SMTP
* **SESSendingResourceValue** - This is the resource name that will be given IAM permission to send raw email via SMTP. This must be a configuration-set name or identity name, depending on **SESSendingResourceCondition**
* * If you used configuration-set, the format for value is:  arn:${Partition}:ses:${Region}:${Account}:configuration-set/${ConfigurationSetName}
* * If you used identity, the format for value is: arn:${Partition}:ses:${Region}:${Account}:identity/${IdentityName}
* **SSMRotationDocument** - The name of the Systems Manager document to use to rotate the password on the relevant servers, for our example we use **MySSMDocument**
* **SSMServerTag** - The name of the Tag to identify which email server on which you'll run the SSM Rotation Document. We use the tag name **EmailServers** 
* **SSMServerTagValue** - The value of the Tag to identify which email server on which you'll run the SSM Rotation Document. We use the tag value **True**.  

```
aws cloudformation deploy --template-file sesautomaticoutput.yaml --stack-name SESAutomaticRotation --parameter-overrides SecretName=sessecret IAMUserName=sessecret SESSendingResourceCondition=identity SESSendingResourceValue=myidentity SSMRotationDocument=MySSMDocument SSMServerTag=EmailServers SSMServerTagValue=True --capabilities CAPABILITY_NAMED_IAM
```

For example, your edited code will look like this: 
```aws cloudformation deploy --template-file sesautomaticoutput.yaml --stack-name SESAutomaticRotation --parameter-overrides SecretName=sessecret IAMUserName=sessecret SESSendingResourceCondition=identity SESSendingResourceValue=myidentity SSMRotationDocument=MySSMDocument SSMServerTag=EmailServer SSMServerTagValue=True --capabilities CAPABILITY_NAMED_IAM```

## Stack Creation

* AWS CloudFormation will provision and configure the resources as defined in the template. This will take about 10 minutes to fully deploy. You can view the status under the stack’s resources tab in the AWS CloudFormation console.
* The template enables automatic secret rotation for the secret based on the MaximumSecretAgeInDays, the exact rotation schedule will be managed by AWS Secrets Manager

NOTE - Note, this solution can be deployed multiple times to generate additional users and secrets to support a scenario where you have more than one AWS SES sending requirement, or want to limit the impact of a compromised credential. Each deployment requires a unique IAMUserName and SecretName.

## Testing the Systems Manager document for your email server(s)
From the AWS Systems Manager console under Documents > Owned by me, 
1. Click on the appropriate document 
2. Use the Run command button in the top right to start the execution process.
3. Ensure the Document is selected, provide the new username and password, select a test instance, and click Run.
4. Verify the intended changes have been made to the instance, and the document is ready to be called from the Lambda function setup by the CloudFormation template.

## Using your own KMS Key

If you make use of your own KMS Key, the Key policy of the Customer Managed Key must allow the IAM role of the Rotation Lambda to perform kms:Decrypt and kms:GenerateDataKey actions. As this role is not created until after the template is deployed just must use the "Rotate Secret Immediately" button to create the first secret once the role has been given the necessary permission to use the KMS key, until that time the Secret will appear as empty in AWS Secrets Manager



## Testing the solution

To test the solution, you can instruct AWS Secrets Manager to perform a rotation immediately. From AWS Secrets Manager console, locate your secret (SESEmailSecret), select "Rotate Secret immediately" from the Rotation tab of the Console.

You can track the progress of the rotation by locating the logs of the Lambda that is deployed to manage the rotation. 

* In the AWS console, go to CloudFormationStack’s Resources tab.
* Find the LogicalID = **SESSecretRotationFunction**.
* Click the Resources tab and click the PhysicalID link for the **SESSecretRotationFunction** Lambda.
* In the Lambda console, click the **Monitor** & click the **View CloudWatch logs** button.
* Open the latest Log stream. The logs should show the rotation flow through 4 steps - ```create_secret, set_secret, test_secret, finish_secret```. More details of each stage are available [here](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html)

## Remediating a compromised credential

A compromised credential can be remediated using the "Rotate Secret Immediately" button under the Rotation tab in the Secrets Manager Console, this will execute an identical process to a normal rotation

# Costs to operate

All AWS services used in this solution have negligible cost, it is likely monthly costs will be well below $1.00 when operating this solution. 




