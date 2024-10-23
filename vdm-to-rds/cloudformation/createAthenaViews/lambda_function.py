import os
import cfnresponse  
import boto3
import time

account_number = os.environ['account_number']
athena_database_name = os.environ['database_name']
output_bucket = os.environ['output_s3_bucket']
table_name = os.environ['glue_table_name']
evaluated_table_name = os.environ['glue_evaluated_table_name']

athena_create_view_queries = [
f'''CREATE OR REPLACE VIEW "dmarc_sorted" AS
SELECT
feedback.report_metadata.org_name org_name
, feedback.report_metadata.email org_email
, feedback.policy_published.domain policy_domain
, CAST(feedback.policy_published.pct AS integer) policy_pct
, feedback.record.row.source_ip record_source_ip
, feedback.record.identifiers.header_from header_from
, feedback.record.identifiers.envelope_from envelope_from
, feedback.record.auth_results.dkim.result dkim_result
, feedback.record.auth_results.spf.result spf_result
, CAST(date_format(from_unixtime(CAST(feedback.report_metadata.date_range.begin AS double)), '%Y-%m-%d') AS date) date_begin
, CAST(date_format(from_unixtime(CAST(feedback.report_metadata.date_range."end" AS double)), '%Y-%m-%d') AS date) date_end
FROM
{athena_database_name}.{table_name}
''',
f'''CREATE OR REPLACE VIEW "dmarc_sorted_evaluated" AS
SELECT
feedback.report_metadata.org_name org_name
, feedback.report_metadata.email org_email
, feedback.policy_published.domain policy_domain
, CAST(feedback.policy_published.pct AS integer) policy_pct
, t.records.row.source_ip record_source_ip
, t.records.identifiers.header_from header_from
, t.records.identifiers.envelope_from envelope_from
, t.records.row.policy_evaluated.dkim dkim_result
, t.records.row.policy_evaluated.spf spf_result
, CAST(date_format(from_unixtime(CAST(feedback.report_metadata.date_range.begin AS double)), '%Y-%m-%d') AS date) date_begin
, CAST(date_format(from_unixtime(CAST(feedback.report_metadata.date_range."end" AS double)), '%Y-%m-%d') AS date) date_end
FROM
({athena_database_name}.{evaluated_table_name}
CROSS JOIN UNNEST(feedback.record) t (records))''',
'''CREATE OR REPLACE VIEW "dmarc_sorted_combined" AS
SELECT * FROM "dmarc_sorted"
UNION ALL
SELECT * FROM "dmarc_sorted_evaluated";''']


def lambda_handler(event, context):
    """
    This function creates the required views in Athena that are used to create the dashboards
    """
    status = cfnresponse.SUCCESS
    failure_reason = ''

    if event['RequestType'] == "Create":

        athena_client = boto3.client("athena")

        try:

            print("Executing queries to create athena views")
            for query in athena_create_view_queries:
                result = athena_client.start_query_execution(QueryString=query,
                                                            QueryExecutionContext={
                                                                'Database': athena_database_name},
                                                            ResultConfiguration={
                                                                'OutputLocation': f's3://{output_bucket}',
                                                                'EncryptionConfiguration': {
                                                                'EncryptionOption': 'SSE_S3',
                                                            }})
                
                execution_id = result['QueryExecutionId']

                # Wait for query to complete
                query_completed = False
                while not query_completed:
                    query_status_result = athena_client.get_query_execution(QueryExecutionId=execution_id)
                    query_status = query_status_result['QueryExecution']['Status']['State']

                    match query_status:
                        case 'QUEUED'|'RUNNING':
                            continue
                        case 'SUCCEEDED':
                            query_completed = True
                        case 'FAILED'|'CANCELLED':
                            query_completed = True
                            status = cfnresponse.FAILED
                            failure_reason = 'Athena query failed or was cancelled'
                            print(f"Athena query status - {query_status}")

                    time.sleep(2)


                if status == cfnresponse.FAILED:
                    break

            print("All views created successfully")

        except Exception as e:
            print(e)
            failure_reason = str(e)
            status = cfnresponse.FAILED

    cfnresponse.send(event, context, status, {}, reason=failure_reason)
    