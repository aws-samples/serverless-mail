## OktaIdCWorkMailLambdaExample

>**BE AWARE:** This code base is an [Open Source](LICENSE) starter project designed to provide a demonstration and a base to start from for specific use cases.
THe code in this sample should not be considered Production-ready.
Do NOT deploy and use this in a Production environment without carefully evaluating all aspects of the solution and getting authorization from your organization's security team.

## Use-case scenario
The example CDK herein is a companion to the AWS blog post [Enable single-sign-on for Amazon WorkMail with IAM Identity Center and Okta](https://aws-blogs-prod.amazon.com/messaging-and-targeting/enable-single-sign-on-for-amazon-workmail-with-iam-identity-center-and-okta-universal-directory/) that describes the process needed to integrate Amazon WorkMail with Okta Identity via IAM IdentityCenter. More information about the AWS CDK is [here](https://aws.amazon.com/cdk/).

The CDK in this project creates and deploys an AWS Lambda in your AWS account that performs users synchronization between IAM IdentityCenter and WorkMail. The Lambda is configured by default to run every 15 minutes, this can be changed via Amazon EventBridge.

## Solution prerequisites
* AWS Account
* AWS IAM user with Administrator permissions
* Python (> v3.x) and Pip (installed by default) [installed and configured on your computer](https://www.python.org/downloads/)
* AWS CLI (v2) [installed and configured on your computer](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* AWS CDK (v2) [installed and configured on your computer](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)

## Solution setup

The instructions that follow guide you deploying a sample solution that programmatically creates/syncs WorkMail users from IAM Identity Center using the AWS CDK CLI. The sample uses naming conventions used in this blog. For example, the Lambda only syncs those users found in the IdC Group named workmail_users. If your IdC group has a different name, or you want to sync multiple IdC groups with WorkMail, you will need to modify the sample code before proceeding

1. Clone this solution to your computer (`git clone https://github.com/aws-samples/serverless-mail/tree/main/idc_okta-workmail`). CD into the  'idc_okta-workmail' directory.

2. Create a virtual environment for packaging in Python:

```bash
python3 -m venv .venv
```

3. Activate the virtual environment:

```bash
source .venv/bin/activate
```

4. Make sure `cdk.json` references the correct path to Python (by default cdk.json refers to `.venv/bin/python app.py`).
    - If you need to locate Python, run this command:

        ```bash
        which python
        ```

5. Install the project dependencies:

```bash
pip3 install -r requirements.txt
```

6. Check the AWS CLI
    - AWS CDK will use AWS CLI local credentials and region.

```bash
aws sts get-caller-identity
```

If you need to change the AWS account, run:

```bash
aws configure
```

7. Prepare the `app.py` file by running:

```bash
python3 get-my-variables.py
```

The ‘get-my-variables.py’ script fetches the necessary variables from your AWS account and create the `app.py` file needed by the CDK. You may want to review the auto-generated `app.py` file for accuracy, especially if the AWS account has been used for other IdC or WorkMail related projects. 

Alternatively, you can skip the 'get-my-variables.py' script and manually populate `app-blank.py` with your account variables, and save the file as `app.py`.

The app.py file requires the following account variables:

- AWS accountId
- AWS Region – the region must be the same for IdC and WorkMail.
IDENTITYSTORE_ID – – found in the Identity Center console under settings or via the AWS CLI aws identitystore list-groups --identity-store-id {identity_store_id}
- IDENTITY_CENTER_INSTANCE_ARN – found in the Identity Center console under settings or via the AWS CLI aws sso-admin list-instances
- IDENTITY_CENTER_APPLICATION_ARN – found in the Identity Center console under Applications or via the AWS CLI aws sso-admin list-applications --instance-arn {instance_arn}`
- WORKMAIL_ORGANIZATION_ID – found in the WorkMail console under Organizations or via the AWS CLI aws workmail list-organizations
- OKTA_GROUP_ID_TO_ASSIGN_TO_WORKMAIL – found in the Identity Center console under Groups > General Information or via the AWS CLI aws identitystore list-groups --identity-store-id {identity_store_id}

8. Bootstrap the package (this step may take several minutes to complete):

```bash
cdk bootstrap
```

9. Synthesize the package (this step may take several minutes to complete):

```bash
cdk synthesize
```

10. Deploy your package (this step may take several minutes to complete):

```bash
cdk deploy
```

Reply "Y" when asked if you want to deploy.

11. Once deployment to your AWS account starts, you can view the deployment status in the CloudFormation console.

### Upon successful deployment

The Lambda deployed by the CD creates/updates/deactivates WorkMail users from those in the IdC group (“workmail_users”) that are being synchronized with your Okta (or other external IP).
    - The Lambda runs immediately on deployment, and every 15 minutes thereafter (this can be modified in EventBridge).
    - If the script finds new/modified/deleted users in IdC (as synced from Okta or other external IP), it will create/modify/deactivate those users in WorkMail.

NOTE - for this example we are only sychronizing WorkMail users that are in (or removed  from) the users in the "workmail_users" IdC group. You may want to modify the project accordingly.


## Clean up

To remove the solution from your account, please follow these steps:

1. Remove CDK Stacks
    - Run `cdk destroy --all`

2. Manually remove IAM IdC users, groups and integration with Okta.
3. Manually remove the Okta application & IAM IdC integration. 

## Do NOT use this example in production as-is

It is critical that before you use any of this code in Production that you work with your own internal Security and Governance teams to conduct the appropriate Code and AppSec reviews for your organization. 

Although the code has been written with best practices in mind, your own company may have additional concerns, rules and restrictions.

You take full ownership and responsibility for the code running in your AWS and Okta environments, and are free to make whatever changes you need to so the solution meets your organization's needs.
