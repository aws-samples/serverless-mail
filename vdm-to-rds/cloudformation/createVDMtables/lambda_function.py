import logging
import pymysql
import os
import cfnresponse

# rds settings
user_name = os.environ['dbuser']
password = os.environ['dbpassword']
mysql_host = os.environ['mysql_host']
db_name = os.environ['db_name']

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """
    This function creates the tables and views for the database that stores VDM data
    """

    status = cfnresponse.SUCCESS
    failure_reason = ''

    if event['RequestType'] == "Create":

        try:
            logger.info("Connecting to database")
            conn = pymysql.connect(host=mysql_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
            with conn.cursor() as cur:
                logger.info('Executing queries to create tables')
                cur.execute(f"use {db_name};")
                cur.execute("drop table if exists isp_volume;")
                logger.info('dropped isp_volume')
                cur.execute("create table isp_volume (ISP varchar(256), DELIVERY_VOLUME int, SEND_VOLUME int, OPEN_VOLUME int, COMPLAINT_VOLUME int, PERMANENT_BOUNCE_VOLUME int, TRANSIENT_BOUNCE_VOLUME int, CLICK_VOLUME int, DELIVERY_OPEN_VOLUME int, DELIVERY_CLICK_VOLUME int, DELIVERY_COMPLAINT_VOLUME int,METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,ISP));")
                logger.info('created isp_volume')
                cur.execute("drop table if exists isp_rate;")
                logger.info('dropped isp_rate')
                cur.execute("create table isp_rate (ISP varchar(256), DELIVERY_RATE varchar(10), SEND_RATE varchar(10), OPEN_RATE varchar(10), COMPLAINT_RATE varchar(10), PERMANENT_BOUNCE_RATE varchar(10), TRANSIENT_BOUNCE_RATE varchar(10), CLICK_RATE varchar(10), DELIVERY_OPEN_RATE varchar(10), DELIVERY_CLICK_RATE varchar(10), DELIVERY_COMPLAINT_RATE varchar(10),METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,ISP));")
                logger.info('created isp_rate')
                cur.execute("drop table if exists email_identity_volume;")
                logger.info('dropped email volume')
                cur.execute("create table email_identity_volume (EMAIL_IDENTITY varchar(256), DELIVERY_VOLUME int, SEND_VOLUME int, OPEN_VOLUME int, COMPLAINT_VOLUME int, PERMANENT_BOUNCE_VOLUME int, TRANSIENT_BOUNCE_VOLUME int, CLICK_VOLUME int, DELIVERY_OPEN_VOLUME int, DELIVERY_CLICK_VOLUME int, DELIVERY_COMPLAINT_VOLUME int,METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,EMAIL_IDENTITY));")
                logger.info('created email volume')
                cur.execute("drop table if exists email_identity_rate;")
                logger.info('dropped email rate')
                cur.execute("create table email_identity_rate (EMAIL_IDENTITY varchar(256), DELIVERY_RATE varchar(10), SEND_RATE varchar(10), OPEN_RATE varchar(10), COMPLAINT_RATE varchar(10), PERMANENT_BOUNCE_RATE varchar(10), TRANSIENT_BOUNCE_RATE varchar(10), CLICK_RATE varchar(10), DELIVERY_OPEN_RATE varchar(10), DELIVERY_CLICK_RATE varchar(10), DELIVERY_COMPLAINT_RATE varchar(10),METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,EMAIL_IDENTITY));")
                logger.info('created email rate')
                cur.execute("drop table if exists configuration_set_volume;")
                logger.info('dropped configuration set volume')
                cur.execute("create table configuration_set_volume (CONFIGURATION_SET varchar(256), DELIVERY_VOLUME int, SEND_VOLUME int, OPEN_VOLUME int, COMPLAINT_VOLUME int, PERMANENT_BOUNCE_VOLUME int, TRANSIENT_BOUNCE_VOLUME int, CLICK_VOLUME int, DELIVERY_OPEN_VOLUME int, DELIVERY_CLICK_VOLUME int, DELIVERY_COMPLAINT_VOLUME int,METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,CONFIGURATION_SET));")
                logger.info('created configuration set volume')
                cur.execute("drop table if exists configuration_set_rate;")
                logger.info('dropped configuration set rate')
                cur.execute("create table configuration_set_rate (CONFIGURATION_SET varchar(256),DELIVERY_RATE varchar(10), SEND_RATE varchar(10), OPEN_RATE varchar(10), COMPLAINT_RATE varchar(10), PERMANENT_BOUNCE_RATE varchar(10), TRANSIENT_BOUNCE_RATE varchar(10), CLICK_RATE varchar(10), DELIVERY_OPEN_RATE varchar(10), DELIVERY_CLICK_RATE varchar(10), DELIVERY_COMPLAINT_RATE varchar(10),METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,CONFIGURATION_SET));")
                logger.info('created configuration set rate')
                conn.commit()
                logger.info('All tables created in database')
        except Exception as e:
            status = cfnresponse.FAILED
            failure_reason = str(e)
    else:
        logger.info('Not a create event, doing nothing')

    # returning status so CloudFormation execution receives the right signals
    cfnresponse.send(event, context, status, {}, reason=failure_reason)
