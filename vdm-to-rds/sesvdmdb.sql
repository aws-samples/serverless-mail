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