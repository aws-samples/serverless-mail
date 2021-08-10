# S/MIME signature validator

This application checks S/MIME signatures of email messages as a solution for the following situations
1. The original message is to modified in transit in a way that the end-user's email client is unable to validate the soon-to-be-broken signature
2. The email is to be be processed by something other than an S/MIME capable email client

This application assumes that the raw email message is stored in S3 and takes the S3 object bucket and key as input, and returns the result.

Optionally, if the SAVE_TO_BUCKET environment variable is set to "True" on the Lambda function, it will save the signature result back to the bucket alongside the email message.

In order to check the signature against one or more trusted certificate authorities, add each CA certificate into a PEM formatted file and upload the file to an S3 bucket to which the Lambda function will have access. Set CACERT_BUCKET and CACERT_KEY accordingly in the function's environment.

This appliication is suitable for integration with Amazon WorkMail or Amazon Simple Email Service, depending on your use case. 

## Build

### Install dependencies

`docker run --rm -v $PWD:/var/task shogo82148/p5-aws-lambda:build-5.34-paws.al2 cpanm --verbose --notest --local-lib extlocal --no-man-pages --installdeps .`

### Build the container

`docker build -t smime .`

### Test locally

Upload sample messages to an S3 bucket. The samples directory has a message you can use if you do not have an S/MIME signed message to work with.

Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN in your environment. Use `set_environment.pl` if you want to use your current session.

Finally, call the function like below, specifying the bucket and key where you stored the sample message.

`docker run --rm -v $PWD:/var/task -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN shogo82148/p5-aws-lambda:5.34-paws.al2 handler.handle '{"bucket":"examplebucket","key":"example.eml"}'`

Optionally, if you have a CA keystore in a PEM formatted file, you can volume mount it for testing by adding the following to the above command:

`-v /path/to/ca/keystore:/tmp/keystore`

## Deploy

### Deploy the container to ECR

Create an ECR repository and make note of the repositoryUri that is returned

`aws ecr create-repository --repository-name examplerepository`

Tag the container with the ECR repositoryUri

`docker tag smime:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/examplerepository:latest`

Login to ECR

`aws ecr get-login-password | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com/examplerepository`

Push the container to ECR

`docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/examplerepository:latest`

### Create the Lambda function

You need to create the function execution role first. You can easily do this via the AWS Console when creating a new Lambda function. 

The role can additionally be given access to the S3 bucket, or you can use an S3 bucket policy.

Example function execution role

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:us-east-1:123456789012:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/examplefunctionname:*"
            ]
        }
    ]
}
```

Example S3 bucket policy

```
{
    "Version": "2012-10-17",
    "Id": "Policy1625828498364",
    "Statement": [
        {
            "Sid": "Stmt1625828495041",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::123456789012:role/service-role/examplefunction-role-cj7nmts2"
            },
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::examplebucket/*"
        }
    ]
}
```

Create the function, specifying the container image URI, the execution role ARN, and a timeout. 

The default timeout is 3 seconds, which is not enough time for this container to start. The max is 900, which is more than enough, but may be required for very large email messages.

```
aws lambda create-function \
    --function-name "examplefunctionname" \
    --code ImageUri=495766005304.dkr.ecr.us-east-1.amazonaws.com/testing1234:latest \
    --package-type Image \
    --timeout 900 \
    --role arn:aws:iam::495766005304:role/service-role/examplefunction-role-cj7nmts2
```

### Update the function with a new container

Here is how you can update the function if you have a new revision of the container pushed to ECR

```
aws lambda update-function-code \
    --function-name "examplefunctionname" \
    --image-uri 495766005304.dkr.ecr.us-east-1.amazonaws.com/testing1234:latest \
    --publish 
```

## Run the Lambda locally

You can verify that the Lambda function is running correctly with this command

`aws lambda invoke --function-name examplefunctionname --payload '{ "bucket": "examplebucket", "key": "example.eml" }' response.json`

## Reference

This project is an example of how to run Perl on AWS Lambda's container runtime using the open source [AWS::Lambda](https://metacpan.org/pod/AWS::Lambda)