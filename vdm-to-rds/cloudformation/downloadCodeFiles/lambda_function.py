import boto3
import urllib.request
import cfnresponse  
from datetime import date, timedelta, datetime     

def download_file(url,filename,bucketname):
    s3 = boto3.client("s3")
    response = urllib.request.urlopen(url)
    file_content = response.read()
    s3.put_object(Bucket=bucketname, Key=filename, Body=file_content)

def lambda_handler(event, context):                
    try:
        bucket = event['ResourceProperties']['bucketname']
        sesvdmbucket = event['ResourceProperties']['sesvdmbucket']
        status = cfnresponse.SUCCESS
        err='worked'

        download_file(url='https://github.com/aws-samples/serverless-mail/blob/main/vdm-to-rds/metricstoMySQL.py?raw=True',filename='packages/metricstoMySQL.py',bucketname=bucket)
        # download importLatestVDM.py for Glue Job
        download_file(url='https://github.com/aws-samples/serverless-mail/blob/main/vdm-to-rds/importLatestVDM.py?raw=True',filename='packages/importLatestVDM.py',bucketname=bucket)
        # download xmldict
        download_file(url='https://github.com/aws-samples/serverless-mail/raw/main/lambda-email-parser/ses-dmarc-email-parser.zip', filename='packages/ses-dmarc-email-parser.zip',bucketname=bucket)
        # create starting lastvdmdate.csv file
        EndDate = date.today()
        s3b = boto3.client("s3")
        s3b.put_object(Bucket=sesvdmbucket, Key='lastvdmdate.csv', Body=(EndDate+ timedelta(days=-7)).isoformat())
    except Exception as e:
        err = repr(e)
        status = cfnresponse.FAILED

    # returning status so CloudFormation execution receives the right signals
    returneddata = {'err':err}
    cfnresponse.send(event, context, status, returneddata)