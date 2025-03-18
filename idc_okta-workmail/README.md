## OktaIdCWorkMailLambdaExample

>**BE AWARE:** This code base is an [Open Source](LICENSE) starter project designed to provide a demonstration and a base to start from for specific use cases.
It should not be considered fully Production-ready.
If you plan to deploy and use this in a Production environment please review the [Using this in Production](#using-this-in-production) section at the end for some additional guidance.

## Use-case scenario
The example CDK herein is a companion to the AWS blog post [Enable single-sign-on for Amazon WorkMail with IAM Identity Center and Okta](https://comingsoon) that describes the process needed to integrate Amazon WorkMail with Okta Identity via IAM IdentityCenter. More information about the AWS CDK is [here](https://aws.amazon.com/cdk/).

The CDK in this project creates and deploys an AWS Lambda in your AWS account that performs users synchronization between IAM IdentityCenter and WorkMail. The Lambda is configured by default to run every 15 minutes, this can be changed via Amazon EventBridge.

## Solution prerequisites
* AWS Account
* AWS IAM user with Administrator permissions
* Python (> v3.x) and Pip (installed by default) [installed and configured on your computer](https://www.python.org/downloads/)
* AWS CLI (v2) [installed and configured on your computer](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
* AWS CDK (v2) [installed and configured on your computer](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)

## Solution setup

The instructions that follow guide you deploying a sample solution that programmatically creates/syncs WorkMail users from IAM Identity Center using the AWS CDK CLI. The sample uses naming conventions used in this blog. For example, the Lambda only syncs those users found in the IdC Group named workmail_users. If your IdC group has a different name, or you want to sync multiple IdC groups with WorkMail, you will need to modify the sample code before proceeding

1. Clone this solution to your computer (using `git clone`), and CD into the  'idc_okta-workmail' directory.

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

The 'get-my-variables.py' script fetches the necessary variables from your AWS account and create the `app.py` file needed by the CDK. You may want to review the auto-generated `app.py` file for accuracy, especially if the AWS account has been used for other IdC or WorkMail related projects.

Alternatively, you can skip the 'get-my-variables.py' script and manually populate `app-blank.py` with your account variables, and save the file as `app.py`.

8. Bootstrap the package (this step may take several minutes to complete):

```bash
cdk bootstrap
```

7. Synthesize the package (this step may take several minutes to complete):

```bash
cdk synthesize
```

8. Deploy your package (this step may take several minutes to complete):

```bash
cdk deploy
```

Reply "Y" when asked if you want to deploy.

Once deployment to your AWS account starts, you can view the deployment status in the CloudFormation console.

### Upon successful deployment

The Lambda deployed by the CD creates/updates/deletes WorkMail users from those in the IdC group (“workmail_users”) that are being synchronized with your Okta (or other external IP).
    - The Lambda runs immediately on deployment, and every 15 minutes thereafter (this can be modified in EventBridge).
    - If the script finds new/modified/deleted users in IdC (as synced from Okta or other external IP), it will create/modify/delete those users in WorkMail.

NOTE - for this example we are only creating WorkMail users for the users in the "workmail_users" IdC group. You may want to modify the project accordingly.


## Clean up

To remove the solution from your account, please follow these steps:

1. Remove CDK Stacks
    - Run `cdk destroy --all`

2. Manually remove 

## Using this in production

It is critical that before you use any of this code in Production that you work with your own internal Security and Governance teams to get the appropriate Code and AppSec reviews for your organization. 

Although the code has been written with best practices in mind, your own company may require different ones, or have additional rules and restrictions.

You take full ownership and responsibility for the code running in your environment, and are free to make whatever changes you need to.