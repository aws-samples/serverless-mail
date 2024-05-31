import sys
import logging
import pymysql
import json
import os
import cfnresponse  

# rds settings
user_name = os.environ['dbuser']
password = os.environ['dbpassword']
mysql_host = os.environ['mysql_host']
db_name = os.environ['db_name']

def lambda_handler(event, context):
    """
    This function creates the tables and views for the sesvdm database
    """
    conn = pymysql.connect(host=mysql_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
    status = cfnresponse.SUCCESS
    err='worked'

    try:
        with conn.cursor() as cur:
            cur.execute("use sesvdm;")
            cur.execute("drop table if exists isp_volume;")
            print('dropped isp_volume')
            cur.execute("create table isp_volume (ISP varchar(256), DELIVERY_VOLUME int, SEND_VOLUME int, OPEN_VOLUME int, COMPLAINT_VOLUME int, PERMANENT_BOUNCE_VOLUME int, TRANSIENT_BOUNCE_VOLUME int, CLICK_VOLUME int, DELIVERY_OPEN_VOLUME int, DELIVERY_CLICK_VOLUME int, DELIVERY_COMPLAINT_VOLUME int,METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,ISP));")
            print('created isp_volume')
            cur.execute("drop table if exists isp_rate;")
            print('dropped isp_rate')
            cur.execute("create table isp_rate (ISP varchar(256), DELIVERY_RATE varchar(10), SEND_RATE varchar(10), OPEN_RATE varchar(10), COMPLAINT_RATE varchar(10), PERMANENT_BOUNCE_RATE varchar(10), TRANSIENT_BOUNCE_RATE varchar(10), CLICK_RATE varchar(10), DELIVERY_OPEN_RATE varchar(10), DELIVERY_CLICK_RATE varchar(10), DELIVERY_COMPLAINT_RATE varchar(10),METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,ISP));")
            print('created isp_rate')
            cur.execute("drop table if exists email_identity_volume;")
            print('dropped email volume')
            cur.execute("create table email_identity_volume (EMAIL_IDENTITY varchar(256), DELIVERY_VOLUME int, SEND_VOLUME int, OPEN_VOLUME int, COMPLAINT_VOLUME int, PERMANENT_BOUNCE_VOLUME int, TRANSIENT_BOUNCE_VOLUME int, CLICK_VOLUME int, DELIVERY_OPEN_VOLUME int, DELIVERY_CLICK_VOLUME int, DELIVERY_COMPLAINT_VOLUME int,METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,EMAIL_IDENTITY));")
            print('created email volume')
            cur.execute("drop table if exists email_identity_rate;")
            print('dropped email rate')
            cur.execute("create table email_identity_rate (EMAIL_IDENTITY varchar(256), DELIVERY_RATE varchar(10), SEND_RATE varchar(10), OPEN_RATE varchar(10), COMPLAINT_RATE varchar(10), PERMANENT_BOUNCE_RATE varchar(10), TRANSIENT_BOUNCE_RATE varchar(10), CLICK_RATE varchar(10), DELIVERY_OPEN_RATE varchar(10), DELIVERY_CLICK_RATE varchar(10), DELIVERY_COMPLAINT_RATE varchar(10),METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,EMAIL_IDENTITY));")
            print('created email rate')
            cur.execute("drop table if exists configuration_set_volume;")
            print('dropped configuration set volume')
            cur.execute("create table configuration_set_volume (CONFIGURATION_SET varchar(256), DELIVERY_VOLUME int, SEND_VOLUME int, OPEN_VOLUME int, COMPLAINT_VOLUME int, PERMANENT_BOUNCE_VOLUME int, TRANSIENT_BOUNCE_VOLUME int, CLICK_VOLUME int, DELIVERY_OPEN_VOLUME int, DELIVERY_CLICK_VOLUME int, DELIVERY_COMPLAINT_VOLUME int,METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,CONFIGURATION_SET));")
            print('created configuration set volume')
            cur.execute("drop table if exists configuration_set_rate;")
            print('dropped configuration set rate')
            cur.execute("create table configuration_set_rate (CONFIGURATION_SET varchar(256),DELIVERY_RATE varchar(10), SEND_RATE varchar(10), OPEN_RATE varchar(10), COMPLAINT_RATE varchar(10), PERMANENT_BOUNCE_RATE varchar(10), TRANSIENT_BOUNCE_RATE varchar(10), CLICK_RATE varchar(10), DELIVERY_OPEN_RATE varchar(10), DELIVERY_CLICK_RATE varchar(10), DELIVERY_COMPLAINT_RATE varchar(10),METRIC_DATE date,IMPORT_DATE date,PRIMARY KEY (METRIC_DATE,CONFIGURATION_SET));")
            print('created configuration set rate')
            cur.execute("drop view if exists vw_configuration_set_consolidated;")
            print('dropped consolidated configuration set view')
            cur.execute("""CREATE VIEW vw_configuration_set_consolidated AS
                SELECT configuration_set_volume.CONFIGURATION_SET,configuration_set_volume.METRIC_DATE,cast(configuration_set_rate.DELIVERY_RATE as UNSIGNED) as CONFIGURATION_SET_DELIVERY_RATE,cast(configuration_set_rate.SEND_RATE as UNSIGNED) as CONFIGURATION_SET_SEND_RATE,cast(configuration_set_rate.OPEN_RATE as UNSIGNED) as CONFIGURATION_SET_OPEN_RATE,cast(configuration_set_rate.COMPLAINT_RATE as UNSIGNED) as CONFIGURATION_SET_COMPLAINT_RATE,cast(configuration_set_rate.PERMANENT_BOUNCE_RATE as UNSIGNED) as CONFIGURATION_SET_PERMANENT_BOUNCE_RATE,cast(configuration_set_rate.TRANSIENT_BOUNCE_RATE as UNSIGNED) as CONFIGURATION_SET_TRANSIENT_BOUNCE_RATE,cast(configuration_set_rate.CLICK_RATE as UNSIGNED) as CONFIGURATION_SET_CLICK_RATE,cast(configuration_set_rate.DELIVERY_OPEN_RATE as UNSIGNED) as CONFIGURATION_SET_DELIVERY_OPEN_RATE,cast(configuration_set_rate.DELIVERY_CLICK_RATE as UNSIGNED) as CONFIGURATION_SET_DELIVERY_CLICK_RATE,cast(configuration_set_rate.DELIVERY_COMPLAINT_RATE as UNSIGNED) as CONFIGURATION_SET_DELIVERY_COMPLAINT_RATE,cast(configuration_set_volume.DELIVERY_VOLUME as UNSIGNED) as CONFIGURATION_SET_DELIVERY_VOLUME,cast(configuration_set_volume.SEND_VOLUME as UNSIGNED) as CONFIGURATION_SET_SEND_VOLUME,cast(configuration_set_volume.OPEN_VOLUME as UNSIGNED) as CONFIGURATION_SET_OPEN_VOLUME,cast(configuration_set_volume.COMPLAINT_VOLUME as UNSIGNED) as CONFIGURATION_SET_COMPLAINT_VOLUME,cast(configuration_set_volume.PERMANENT_BOUNCE_VOLUME as UNSIGNED) as CONFIGURATION_SET_PERMANENT_BOUNCE_VOLUME,cast(configuration_set_volume.TRANSIENT_BOUNCE_VOLUME as UNSIGNED) as CONFIGURATION_SET_TRANSIENT_BOUNCE_VOLUME,cast(configuration_set_volume.CLICK_VOLUME as UNSIGNED) as CONFIGURATION_SET_CLICK_VOLUME,cast(configuration_set_volume.DELIVERY_OPEN_VOLUME as UNSIGNED) as CONFIGURATION_SET_DELIVERY_OPEN_VOLUME,cast(configuration_set_volume.DELIVERY_CLICK_VOLUME as UNSIGNED) as CONFIGURATION_SET_DELIVERY_CLICK_VOLUME,cast(configuration_set_volume.DELIVERY_COMPLAINT_VOLUME as UNSIGNED) as CONFIGURATION_SET_DELIVERY_COMPLAINT_VOLUME
                FROM configuration_set_volume LEFT JOIN configuration_set_rate on configuration_set_volume.METRIC_DATE = configuration_set_rate.METRIC_DATE and configuration_set_volume.CONFIGURATION_SET = configuration_set_rate.CONFIGURATION_SET;""")
            print('created consolidated configuration set view')
            cur.execute("drop view if exists vw_email_identity_consolidated;")
            print('dropped consolidated email identity view')
            cur.execute("""CREATE VIEW vw_email_identity_consolidated AS
                SELECT email_identity_rate.EMAIL_IDENTITY,email_identity_rate.METRIC_DATE,cast(email_identity_rate.DELIVERY_RATE as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_RATE,cast(email_identity_rate.SEND_RATE as UNSIGNED) as EMAIL_IDENTITY_SEND_RATE,cast(email_identity_rate.OPEN_RATE as UNSIGNED) as EMAIL_IDENTITY_OPEN_RATE,cast(email_identity_rate.COMPLAINT_RATE as UNSIGNED) as EMAIL_IDENTITY_COMPLAINT_RATE,cast(email_identity_rate.PERMANENT_BOUNCE_RATE as UNSIGNED) as EMAIL_IDENTITY_PERMANENT_BOUNCE_RATE,cast(email_identity_rate.TRANSIENT_BOUNCE_RATE as UNSIGNED) as EMAIL_IDENTITY_TRANSIENT_BOUNCE_RATE,cast(email_identity_rate.CLICK_RATE as UNSIGNED) as EMAIL_IDENTITY_CLICK_RATE,cast(email_identity_rate.DELIVERY_OPEN_RATE as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_OPEN_RATE,cast(email_identity_rate.DELIVERY_CLICK_RATE as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_CLICK_RATE,cast(email_identity_rate.DELIVERY_COMPLAINT_RATE as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_COMPLAINT_RATE,cast(email_identity_volume.DELIVERY_VOLUME as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_VOLUME,cast(email_identity_volume.SEND_VOLUME as UNSIGNED) as EMAIL_IDENTITY_SEND_VOLUME,cast(email_identity_volume.OPEN_VOLUME as UNSIGNED) as EMAIL_IDENTITY_OPEN_VOLUME,cast(email_identity_volume.COMPLAINT_VOLUME as UNSIGNED) as EMAIL_IDENTITY_COMPLAINT_VOLUME,cast(email_identity_volume.PERMANENT_BOUNCE_VOLUME as UNSIGNED) as EMAIL_IDENTITY_PERMANENT_BOUNCE_VOLUME,cast(email_identity_volume.TRANSIENT_BOUNCE_VOLUME as UNSIGNED) as EMAIL_IDENTITY_TRANSIENT_BOUNCE_VOLUME,cast(email_identity_volume.CLICK_VOLUME as UNSIGNED) as EMAIL_IDENTITY_CLICK_VOLUME,cast(email_identity_volume.DELIVERY_OPEN_VOLUME as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_OPEN_VOLUME,cast(email_identity_volume.DELIVERY_CLICK_VOLUME as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_CLICK_VOLUME,cast(email_identity_volume.DELIVERY_COMPLAINT_VOLUME as UNSIGNED) as EMAIL_IDENTITY_DELIVERY_COMPLAINT_VOLUME
                FROM email_identity_rate LEFT JOIN email_identity_volume on email_identity_rate.METRIC_DATE = email_identity_volume.METRIC_DATE and email_identity_rate.EMAIL_IDENTITY = email_identity_volume.EMAIL_IDENTITY;""")
            print('created consolidated email identity view')
            cur.execute("drop view if exists vw_isp_consolidated;")
            print('dropped consolidated isp view')
            cur.execute("""CREATE VIEW vw_isp_consolidated AS
                SELECT isp_rate.ISP as ISP,isp_rate.METRIC_DATE,cast(isp_rate.DELIVERY_RATE as UNSIGNED) as ISP_DELIVERY_RATE,cast(isp_rate.SEND_RATE as UNSIGNED) as ISP_SEND_RATE,cast(isp_rate.OPEN_RATE as UNSIGNED) as ISP_OPEN_RATE,cast(isp_rate.COMPLAINT_RATE as UNSIGNED) as ISP_COMPLAINT_RATE,cast(isp_rate.PERMANENT_BOUNCE_RATE as UNSIGNED) as ISP_PERMANENT_BOUNCE_RATE,cast(isp_rate.TRANSIENT_BOUNCE_RATE as UNSIGNED) as ISP_TRANSIENT_BOUNCE_RATE,cast(isp_rate.CLICK_RATE as UNSIGNED) as ISP_CLICK_RATE,cast(isp_rate.DELIVERY_OPEN_RATE as UNSIGNED) as ISP_DELIVERY_OPEN_RATE,cast(isp_rate.DELIVERY_CLICK_RATE as UNSIGNED) as ISP_DELIVERY_CLICK_RATE,cast(isp_rate.DELIVERY_COMPLAINT_RATE as UNSIGNED) as ISP_DELIVERY_COMPLAINT_RATE,cast(isp_volume.DELIVERY_VOLUME as UNSIGNED) as ISP_DELIVERY_VOLUME,cast(isp_volume.SEND_VOLUME as UNSIGNED) as ISP_SEND_VOLUME,cast(isp_volume.OPEN_VOLUME as UNSIGNED) as ISP_OPEN_VOLUME,cast(isp_volume.COMPLAINT_VOLUME as UNSIGNED) as ISP_COMPLAINT_VOLUME,cast(isp_volume.PERMANENT_BOUNCE_VOLUME as UNSIGNED) as ISP_PERMANENT_BOUNCE_VOLUME,cast(isp_volume.TRANSIENT_BOUNCE_VOLUME as UNSIGNED) as ISP_TRANSIENT_BOUNCE_VOLUME,cast(isp_volume.CLICK_VOLUME as UNSIGNED) as ISP_CLICK_VOLUME,cast(isp_volume.DELIVERY_OPEN_VOLUME as UNSIGNED) as ISP_DELIVERY_OPEN_VOLUME,cast(isp_volume.DELIVERY_CLICK_VOLUME as UNSIGNED) as ISP_DELIVERY_CLICK_VOLUME,cast(isp_volume.DELIVERY_COMPLAINT_VOLUME as UNSIGNED) as ISP_DELIVERY_COMPLAINT_VOLUME
                FROM isp_rate LEFT JOIN isp_volume on isp_rate.METRIC_DATE = isp_volume.METRIC_DATE and isp_rate.ISP = isp_volume.ISP;""")
            print('created consolidated isp view')
            conn.commit()
    except Exception as e:
        err = repr(e)
        status = cfnresponse.FAILED

    # returning status so CloudFormation execution receives the right signals
    returneddata = {'err':err}
    cfnresponse.send(event, context, status, returneddata)
    