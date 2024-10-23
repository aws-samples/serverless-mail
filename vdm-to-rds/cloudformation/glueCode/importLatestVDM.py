import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from datetime import date, timedelta, datetime
import time
import requests
import boto3

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME','bucketname'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
logger = glueContext.get_logger()
    
s3 = boto3.client('s3')
sesv2 = boto3.client('sesv2')
logger.info("boto3version:" + boto3.__version__)

# set variables for later use
bucket = args['bucketname']
date_filename = 'lastvdmdate.csv'

# Check if the data_filename exists or if this is first run
objectList = s3.list_objects_v2(Bucket=bucket, Prefix=date_filename)
if not objectList['KeyCount']:
    # File does not exist, create it
    EndDate = date.today()
    s3.put_object(Bucket=bucket, Key=date_filename, Body=(EndDate + timedelta(days=-7)).isoformat())


# Get dates for the current run based on the last run
datedyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://{}/{}".format(bucket, date_filename)]},
    format="csv"
)
datedf = datedyf.toDF()
lastEndDate = datedf.agg({"col0": "max"}).collect()[0][0]
lastEndDate = datetime.strptime(lastEndDate, '%Y-%m-%d').date()
StartDate = lastEndDate + timedelta(days=1)
EndDate = date.today()
# VDM keeps 60 days of data. Adjusting date to capture last 60 days in the case the StartDate is older than that
if (StartDate < EndDate - timedelta(days=60)):
    StartDate = EndDate - timedelta(days=60)

# Loop through all dates since the start date to ensure data is gathered for the accurate date of measurement
while StartDate < EndDate:
    logger.info("StartDate: " + StartDate.isoformat())
    # build the ISP/VOLUME statement and create the export job
    ispvolres = sesv2.create_export_job(
        ExportDataSource={
            'MetricsDataSource': {
                'Dimensions': {
                    "ISP": ["*"]
                },
                'Namespace': 'VDM',
                'Metrics': [
                    {
                    "Name": "DELIVERY",
                    "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "SEND",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "OPEN",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "COMPLAINT",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "PERMANENT_BOUNCE",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "TRANSIENT_BOUNCE",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "CLICK",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_OPEN",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_CLICK",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_COMPLAINT",
                        "Aggregation": "VOLUME"
                    }
                    ],
                "StartDate": StartDate.isoformat(),
                "EndDate": (StartDate + timedelta(days=1)).isoformat()
            }
        },
        ExportDestination={
            'DataFormat': 'CSV'
        }
    )

    # keep retrieving the job information until it is completed
    jobstatus = 'CREATED'
    while jobstatus != 'COMPLETED': 
        jobstatus = sesv2.get_export_job(JobId=ispvolres['JobId'])['JobStatus']
        print(jobstatus)
        time.sleep(5)
    ispvolfile = requests.get(sesv2.get_export_job(JobId=ispvolres['JobId'])['ExportDestination']['S3Url'])    
    # Upload the result files
    s3.put_object(Bucket=bucket, Key="isp_volume.{}.csv".format(StartDate.isoformat()), Body=ispvolfile.content)

    # build the ISP/RATE statement and create the export job
    ispratres = sesv2.create_export_job(
        ExportDataSource={
            'MetricsDataSource': {
                'Dimensions': {
                    "ISP": ["*"]
                },
                'Namespace': 'VDM',
                'Metrics': [
                    {
                    "Name": "DELIVERY",
                    "Aggregation": "RATE"
                    },
                    {
                        "Name": "SEND",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "OPEN",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "COMPLAINT",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "PERMANENT_BOUNCE",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "TRANSIENT_BOUNCE",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "CLICK",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_OPEN",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_CLICK",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_COMPLAINT",
                        "Aggregation": "RATE"
                    }
                    ],
                "StartDate": StartDate.isoformat(),
                "EndDate": (StartDate + timedelta(days=1)).isoformat()
            }
        },
        ExportDestination={
            'DataFormat': 'CSV'
        }
    )

    # keep retrieving the job information until it is completed
    jobstatus = 'CREATED'
    while jobstatus != 'COMPLETED': 
        jobstatus = sesv2.get_export_job(JobId=ispratres['JobId'])['JobStatus']
        print(jobstatus)
        time.sleep(5)
    ispratfile = requests.get(sesv2.get_export_job(JobId=ispratres['JobId'])['ExportDestination']['S3Url'])  
    # Upload the result files
    s3.put_object(Bucket=bucket, Key="isp_rate.{}.csv".format(StartDate.isoformat()), Body=ispratfile.content)

    # build the EMAIL_IDENTITY/VOLUME statement and create the export job
    emivolres = sesv2.create_export_job(
        ExportDataSource={
            'MetricsDataSource': {
                'Dimensions': {
                    "EMAIL_IDENTITY": ["*"]
                },
                'Namespace': 'VDM',
                'Metrics': [
                    {
                    "Name": "DELIVERY",
                    "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "SEND",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "OPEN",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "COMPLAINT",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "PERMANENT_BOUNCE",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "TRANSIENT_BOUNCE",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "CLICK",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_OPEN",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_CLICK",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_COMPLAINT",
                        "Aggregation": "VOLUME"
                    }
                    ],
                "StartDate": StartDate.isoformat(),
                "EndDate": (StartDate + timedelta(days=1)).isoformat()
            }
        },
        ExportDestination={
            'DataFormat': 'CSV'
        }
    )

    # keep retrieving the job information until it is completed
    jobstatus = 'CREATED'
    while jobstatus != 'COMPLETED': 
        jobstatus = sesv2.get_export_job(JobId=emivolres['JobId'])['JobStatus']
        print(jobstatus)
        time.sleep(5)
    emivolfile = requests.get(sesv2.get_export_job(JobId=emivolres['JobId'])['ExportDestination']['S3Url'])
    # Upload the result files
    s3.put_object(Bucket=bucket, Key="email_identity_volume.{}.csv".format(StartDate.isoformat()), Body=emivolfile.content)

    # build the EMAIL_IDENTITY/RATE statement and create the export job
    emirateres = sesv2.create_export_job(
        ExportDataSource={
            'MetricsDataSource': {
                'Dimensions': {
                    "EMAIL_IDENTITY": ["*"]
                },
                'Namespace': 'VDM',
                'Metrics': [
                    {
                    "Name": "DELIVERY",
                    "Aggregation": "RATE"
                    },
                    {
                        "Name": "SEND",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "OPEN",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "COMPLAINT",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "PERMANENT_BOUNCE",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "TRANSIENT_BOUNCE",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "CLICK",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_OPEN",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_CLICK",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_COMPLAINT",
                        "Aggregation": "RATE"
                    }
                    ],
                "StartDate": StartDate.isoformat(),
                "EndDate": (StartDate + timedelta(days=1)).isoformat()
            }
        },
        ExportDestination={
            'DataFormat': 'CSV'
        }
    )

    # keep retrieving the job information until it is completed
    jobstatus = 'CREATED'
    while jobstatus != 'COMPLETED': 
        jobstatus = sesv2.get_export_job(JobId=emirateres['JobId'])['JobStatus']
        print(jobstatus)
        time.sleep(5)
    emiratefile = requests.get(sesv2.get_export_job(JobId=emirateres['JobId'])['ExportDestination']['S3Url'])
    # Upload the result files
    s3.put_object(Bucket=bucket, Key="email_identity_rate.{}.csv".format(StartDate.isoformat()), Body=emiratefile.content)

    # build the CONFIGURATION_SET/VOLUME statement and create the export job
    configvolumres = sesv2.create_export_job(
        ExportDataSource={
            'MetricsDataSource': {
                'Dimensions': {
                    "CONFIGURATION_SET": ["*"]
                },
                'Namespace': 'VDM',
                'Metrics': [
                    {
                    "Name": "DELIVERY",
                    "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "SEND",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "OPEN",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "COMPLAINT",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "PERMANENT_BOUNCE",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "TRANSIENT_BOUNCE",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "CLICK",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_OPEN",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_CLICK",
                        "Aggregation": "VOLUME"
                    },
                    {
                        "Name": "DELIVERY_COMPLAINT",
                        "Aggregation": "VOLUME"
                    }
                    ],
                "StartDate": StartDate.isoformat(),
                "EndDate": (StartDate + timedelta(days=1)).isoformat()
            }
        },
        ExportDestination={
            'DataFormat': 'CSV'
        }
    )

    # keep retrieving the job information until it is completed
    jobstatus = 'CREATED'
    while jobstatus != 'COMPLETED': 
        jobstatus = sesv2.get_export_job(JobId=configvolumres['JobId'])['JobStatus']
        print(jobstatus)
        time.sleep(5)
    configvolumfile = requests.get(sesv2.get_export_job(JobId=configvolumres['JobId'])['ExportDestination']['S3Url'])
    # Upload the result files
    s3.put_object(Bucket=bucket, Key="configuration_set_volume.{}.csv".format(StartDate.isoformat()), Body=configvolumfile.content)

    # build the CONFIGURATION_SET/RATE statement and create the export job
    configrateres = sesv2.create_export_job(
        ExportDataSource={
            'MetricsDataSource': {
                'Dimensions': {
                    "CONFIGURATION_SET": ["*"]
                },
                'Namespace': 'VDM',
                'Metrics': [
                    {
                    "Name": "DELIVERY",
                    "Aggregation": "RATE"
                    },
                    {
                        "Name": "SEND",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "OPEN",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "COMPLAINT",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "PERMANENT_BOUNCE",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "TRANSIENT_BOUNCE",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "CLICK",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_OPEN",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_CLICK",
                        "Aggregation": "RATE"
                    },
                    {
                        "Name": "DELIVERY_COMPLAINT",
                        "Aggregation": "RATE"
                    }
                    ],
                "StartDate": StartDate.isoformat(),
                "EndDate": (StartDate + timedelta(days=1)).isoformat()
            }
        },
        ExportDestination={
            'DataFormat': 'CSV'
        }
    )

    # keep retrieving the job information until it is completed
    jobstatus = 'CREATED'
    while jobstatus != 'COMPLETED': 
        jobstatus = sesv2.get_export_job(JobId=configrateres['JobId'])['JobStatus']
        print(jobstatus)
        time.sleep(5)
    configratefile = requests.get(sesv2.get_export_job(JobId=configrateres['JobId'])['ExportDestination']['S3Url'])
    # Upload the result files
    s3.put_object(Bucket=bucket, Key="configuration_set_rate.{}.csv".format(StartDate.isoformat()), Body=configratefile.content)

    #increment the date to get the next day
    StartDate = StartDate + timedelta(days=1)
    
# Update the last date run after everything is imported
s3.put_object(Bucket=bucket, Key=date_filename, Body=(EndDate+ timedelta(days=-1)).isoformat())

job.commit()
