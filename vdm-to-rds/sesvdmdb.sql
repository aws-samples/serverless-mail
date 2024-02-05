create database sesvdm;

use sesvdm;

drop table if exists isp_volume;
create table isp_volume (
    ISP varchar(256), 
    DELIVERY_VOLUME int, 
    SEND_VOLUME int, 
    OPEN_VOLUME int, 
    COMPLAINT_VOLUME int, 
    PERMANENT_BOUNCE_VOLUME int, 
    TRANSIENT_BOUNCE_VOLUME int, 
    CLICK_VOLUME int, 
    DELIVERY_OPEN_VOLUME int, 
    DELIVERY_CLICK_VOLUME int, 
    DELIVERY_COMPLAINT_VOLUME int,
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE,ISP)
);

drop table if exists isp_rate;
create table isp_rate (
    ISP varchar(256), 
    DELIVERY_RATE varchar(10), 
    SEND_RATE varchar(10), 
    OPEN_RATE varchar(10), 
    COMPLAINT_RATE varchar(10), 
    PERMANENT_BOUNCE_RATE varchar(10), 
    TRANSIENT_BOUNCE_RATE varchar(10), 
    CLICK_RATE varchar(10), 
    DELIVERY_OPEN_RATE varchar(10), 
    DELIVERY_CLICK_RATE varchar(10), 
    DELIVERY_COMPLAINT_RATE varchar(10),
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE,ISP)
);

drop table if exists email_identity_volume;
create table email_identity_volume (
    EMAIL_IDENTITY varchar(256), 
    DELIVERY_VOLUME int, 
    SEND_VOLUME int, 
    OPEN_VOLUME int, 
    COMPLAINT_VOLUME int, 
    PERMANENT_BOUNCE_VOLUME int, 
    TRANSIENT_BOUNCE_VOLUME int, 
    CLICK_VOLUME int, 
    DELIVERY_OPEN_VOLUME int, 
    DELIVERY_CLICK_VOLUME int, 
    DELIVERY_COMPLAINT_VOLUME int,
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE,EMAIL_IDENTITY)
);

drop table if exists email_identity_rate;
create table email_identity_rate (
    EMAIL_IDENTITY varchar(256), 
    DELIVERY_RATE varchar(10), 
    SEND_RATE varchar(10), 
    OPEN_RATE varchar(10), 
    COMPLAINT_RATE varchar(10), 
    PERMANENT_BOUNCE_RATE varchar(10), 
    TRANSIENT_BOUNCE_RATE varchar(10), 
    CLICK_RATE varchar(10), 
    DELIVERY_OPEN_RATE varchar(10), 
    DELIVERY_CLICK_RATE varchar(10), 
    DELIVERY_COMPLAINT_RATE varchar(10),
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE,EMAIL_IDENTITY)
);

drop table if exists configuration_set_volume;
create table configuration_set_volume (
    CONFIGURATION_SET varchar(256), 
    DELIVERY_VOLUME int, 
    SEND_VOLUME int, 
    OPEN_VOLUME int, 
    COMPLAINT_VOLUME int, 
    PERMANENT_BOUNCE_VOLUME int, 
    TRANSIENT_BOUNCE_VOLUME int, 
    CLICK_VOLUME int, 
    DELIVERY_OPEN_VOLUME int, 
    DELIVERY_CLICK_VOLUME int, 
    DELIVERY_COMPLAINT_VOLUME int,
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE,CONFIGURATION_SET)
);

drop table if exists configuration_set_rate;
create table configuration_set_rate (
    CONFIGURATION_SET varchar(256),
    DELIVERY_RATE varchar(10), 
    SEND_RATE varchar(10), 
    OPEN_RATE varchar(10), 
    COMPLAINT_RATE varchar(10), 
    PERMANENT_BOUNCE_RATE varchar(10), 
    TRANSIENT_BOUNCE_RATE varchar(10), 
    CLICK_RATE varchar(10), 
    DELIVERY_OPEN_RATE varchar(10), 
    DELIVERY_CLICK_RATE varchar(10), 
    DELIVERY_COMPLAINT_RATE varchar(10),
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE,CONFIGURATION_SET)
);

drop table if exists dmarc_sorted;
create table dmarc_sorted (
    org_name varchar(256), 
    org_email varchar(256), 
    policy_domain varchar(256), 
    policy_pct int, 
    record_source_ip varchar(256), 
    header_from varchar(256),
    envelope_from varchar(256), 
    dkim_result varchar(256), 
    spf_result varchar(256), 
    date_begin date, 
    date_end date,
    METRIC_DATE date,
    IMPORT_DATE date,
    PRIMARY KEY (METRIC_DATE)
);



CREATE VIEW vw_configuration_set_consolidated AS
SELECT
	configuration_set_volume.CONFIGURATION_SET,
	configuration_set_volume.METRIC_DATE,
	configuration_set_rate.DELIVERY_RATE as CONFIGURATION_SET_DELIVERY_RATE,
	configuration_set_rate.SEND_RATE as CONFIGURATION_SET_SEND_RATE,
	configuration_set_rate.OPEN_RATE as CONFIGURATION_SET_OPEN_RATE,
	configuration_set_rate.COMPLAINT_RATE as CONFIGURATION_SET_COMPLAINT_RATE,
	configuration_set_rate.PERMANENT_BOUNCE_RATE as CONFIGURATION_SET_PERMANENT_BOUNCE_RATE,
	configuration_set_rate.TRANSIENT_BOUNCE_RATE as CONFIGURATION_SET_TRANSIENT_BOUNCE_RATE,
	configuration_set_rate.CLICK_RATE as CONFIGURATION_SET_CLICK_RATE,
	configuration_set_rate.DELIVERY_OPEN_RATE as CONFIGURATION_SET_DELIVERY_OPEN_RATE,
	configuration_set_rate.DELIVERY_CLICK_RATE as CONFIGURATION_SET_DELIVERY_CLICK_RATE,
	configuration_set_rate.DELIVERY_COMPLAINT_RATE as CONFIGURATION_SET_DELIVERY_COMPLAINT_RATE,
	configuration_set_volume.DELIVERY_VOLUME as CONFIGURATION_SET_DELIVERY_VOLUME,
	configuration_set_volume.SEND_VOLUME as CONFIGURATION_SET_SEND_VOLUME,
	configuration_set_volume.OPEN_VOLUME as CONFIGURATION_SET_OPEN_VOLUME,
	configuration_set_volume.COMPLAINT_VOLUME as CONFIGURATION_SET_COMPLAINT_VOLUME,
	configuration_set_volume.PERMANENT_BOUNCE_VOLUME as CONFIGURATION_SET_PERMANENT_BOUNCE_VOLUME,
	configuration_set_volume.TRANSIENT_BOUNCE_VOLUME as CONFIGURATION_SET_TRANSIENT_BOUNCE_VOLUME,
	configuration_set_volume.CLICK_VOLUME as CONFIGURATION_SET_CLICK_VOLUME,
	configuration_set_volume.DELIVERY_OPEN_VOLUME as CONFIGURATION_SET_DELIVERY_OPEN_VOLUME,
	configuration_set_volume.DELIVERY_CLICK_VOLUME as CONFIGURATION_SET_DELIVERY_CLICK_VOLUME,
	configuration_set_volume.DELIVERY_COMPLAINT_VOLUME as CONFIGURATION_SET_DELIVERY_COMPLAINT_VOLUME
FROM configuration_set_volume
LEFT JOIN configuration_set_rate on configuration_set_volume.METRIC_DATE = configuration_set_rate.METRIC_DATE
	and configuration_set_volume.CONFIGURATION_SET = configuration_set_rate.CONFIGURATION_SET;

CREATE VIEW vw_email_identity_consolidated AS
SELECT
	email_identity_rate.EMAIL_IDENTITY,
	email_identity_rate.METRIC_DATE,
	email_identity_rate.DELIVERY_RATE as EMAIL_IDENTITY_DELIVERY_RATE,
	email_identity_rate.SEND_RATE as EMAIL_IDENTITY_SEND_RATE,
	email_identity_rate.OPEN_RATE as EMAIL_IDENTITY_OPEN_RATE,
	email_identity_rate.COMPLAINT_RATE as EMAIL_IDENTITY_COMPLAINT_RATE,
	email_identity_rate.PERMANENT_BOUNCE_RATE as EMAIL_IDENTITY_PERMANENT_BOUNCE_RATE,
	email_identity_rate.TRANSIENT_BOUNCE_RATE as EMAIL_IDENTITY_TRANSIENT_BOUNCE_RATE,
	email_identity_rate.CLICK_RATE as EMAIL_IDENTITY_CLICK_RATE,
	email_identity_rate.DELIVERY_OPEN_RATE as EMAIL_IDENTITY_DELIVERY_OPEN_RATE,
	email_identity_rate.DELIVERY_CLICK_RATE as EMAIL_IDENTITY_DELIVERY_CLICK_RATE,
	email_identity_rate.DELIVERY_COMPLAINT_RATE as EMAIL_IDENTITY_DELIVERY_COMPLAINT_RATE,
	email_identity_volume.DELIVERY_VOLUME as EMAIL_IDENTITY_DELIVERY_VOLUME,
	email_identity_volume.SEND_VOLUME as EMAIL_IDENTITY_SEND_VOLUME,
	email_identity_volume.OPEN_VOLUME as EMAIL_IDENTITY_OPEN_VOLUME,
	email_identity_volume.COMPLAINT_VOLUME as EMAIL_IDENTITY_COMPLAINT_VOLUME,
	email_identity_volume.PERMANENT_BOUNCE_VOLUME as EMAIL_IDENTITY_PERMANENT_BOUNCE_VOLUME,
	email_identity_volume.TRANSIENT_BOUNCE_VOLUME as EMAIL_IDENTITY_TRANSIENT_BOUNCE_VOLUME,
	email_identity_volume.CLICK_VOLUME as EMAIL_IDENTITY_CLICK_VOLUME,
	email_identity_volume.DELIVERY_OPEN_VOLUME as EMAIL_IDENTITY_DELIVERY_OPEN_VOLUME,
	email_identity_volume.DELIVERY_CLICK_VOLUME as EMAIL_IDENTITY_DELIVERY_CLICK_VOLUME,
	email_identity_volume.DELIVERY_COMPLAINT_VOLUME as EMAIL_IDENTITY_DELIVERY_COMPLAINT_VOLUME
FROM email_identity_rate
LEFT JOIN email_identity_volume on email_identity_rate.METRIC_DATE = email_identity_volume.METRIC_DATE
	and email_identity_rate.EMAIL_IDENTITY = email_identity_volume.EMAIL_IDENTITY;

CREATE VIEW vw_isp_consolidated AS
SELECT
	isp_rate.ISP as ISP,
	isp_rate.METRIC_DATE,
	isp_rate.DELIVERY_RATE as ISP_DELIVERY_RATE,
	isp_rate.SEND_RATE as ISP_SEND_RATE,
	isp_rate.OPEN_RATE as ISP_OPEN_RATE,
	isp_rate.COMPLAINT_RATE as ISP_COMPLAINT_RATE,
	isp_rate.PERMANENT_BOUNCE_RATE as ISP_PERMANENT_BOUNCE_RATE,
	isp_rate.TRANSIENT_BOUNCE_RATE as ISP_TRANSIENT_BOUNCE_RATE,
	isp_rate.CLICK_RATE as ISP_CLICK_RATE,
	isp_rate.DELIVERY_OPEN_RATE as ISP_DELIVERY_OPEN_RATE,
	isp_rate.DELIVERY_CLICK_RATE as ISP_DELIVERY_CLICK_RATE,
	isp_rate.DELIVERY_COMPLAINT_RATE as ISP_DELIVERY_COMPLAINT_RATE,
	isp_volume.DELIVERY_VOLUME as ISP_DELIVERY_VOLUME,
	isp_volume.SEND_VOLUME as ISP_SEND_VOLUME,
	isp_volume.OPEN_VOLUME as ISP_OPEN_VOLUME,
	isp_volume.COMPLAINT_VOLUME as ISP_COMPLAINT_VOLUME,
	isp_volume.PERMANENT_BOUNCE_VOLUME as ISP_PERMANENT_BOUNCE_VOLUME,
	isp_volume.TRANSIENT_BOUNCE_VOLUME as ISP_TRANSIENT_BOUNCE_VOLUME,
	isp_volume.CLICK_VOLUME as ISP_CLICK_VOLUME,
	isp_volume.DELIVERY_OPEN_VOLUME as ISP_DELIVERY_OPEN_VOLUME,
	isp_volume.DELIVERY_CLICK_VOLUME as ISP_DELIVERY_CLICK_VOLUME,
	isp_volume.DELIVERY_COMPLAINT_VOLUME as ISP_DELIVERY_COMPLAINT_VOLUME
FROM isp_rate
LEFT JOIN isp_volume on isp_rate.METRIC_DATE = isp_volume.METRIC_DATE
	and isp_rate.ISP = isp_volume.ISP;
