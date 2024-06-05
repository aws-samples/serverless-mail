import os
import boto3
import email
import json
import re
import uuid
import xmltodict
import gzip
from io import BytesIO
import io


# added json conversion - jhblee@

s3 = boto3.client("s3")
workmail_message_flow = boto3.client('workmailmessageflow')

def unzip_gz_content(gz_content):
  with gzip.open(io.BytesIO(gz_content), "rb") as f:
    return f.read()
    
def xml_to_json(xml_string):
   data_dict = xmltodict.parse(xml_string)
   # json_data = json.dumps(data_dict, indent=4) Athena only handled single link JSON
   json_data = json.dumps(data_dict, separators=(',', ':'))
   return json_data
    
def lambda_handler(event, context):
   print(json.dumps(event))
   destination_bucket = os.environ.get('destination_bucket')
   dmarc_report_bucket = os.environ.get('dmarc_report_bucket')
   dmarc_report_bucket_folder = os.environ.get('dmarc_report_bucket_folder')
   source_bucket = os.environ.get('source_bucket')
   key_prefix = None
   if not destination_bucket:
      print("Environment variable missing: destination_bucket")
      return
   
   try:   
      # keep track of how many MIME parts are parsed and saved to S3
      saved_parts = 0
      msg = None
      parts = None
      workmail_mutate = None

      # event is from workmail
      if event.get('messageId'):
         message_id = event['messageId']
         key_prefix = message_id
         raw_msg = workmail_message_flow.get_raw_message_content(messageId=message_id)
         msg = email.message_from_bytes(raw_msg['messageContent'].read())
         if os.environ.get('modify_workmail_message'):
            workmail_mutate = True

      # event is from s3
      else:
         records = event.get('Records', [])
         record  = records[0]
         # TODO: for record in records:
         # get the S3 object information
         s3_info = record['s3']
         object_info = s3_info['object']
         if s3_info['bucket']['name'] == destination_bucket:
            print("To prevent recursive file creation this function will not write back to the same bucket")
            return {
               'statusCode': 400,
               'body': 'To prevent recursive file creation this function will not write back to the same bucket'
            }
         
         # get the email message stored in S3 and parse it using the python email library
         # TODO: error condition - if the file isn't an email message or doesn't parse correctly
         fileObj, object_key = [None] * 2
         object_key = object_info['key']
         key_prefix = object_key
         fileObj = s3.get_object(Bucket = s3_info['bucket']['name'], Key = object_key)
         msg = email.message_from_bytes(fileObj['Body'].read())
      
      # save the headers of the message to the bucket
      headers_to_save = None
      # By default saving all headers, but use environment vairables to be more specific
      if os.environ.get('select_headers','ALL'): 
         headers_to_save = re.split(',\s*', str(os.environ.get('select_headers', 'ALL')))
         all_headers = msg.items()
         if "ALL" in headers_to_save:
            s3.put_object(Bucket = destination_bucket, Key = key_prefix + "/headers.json", Body = json.dumps(all_headers))
         elif len(headers_to_save) > 0:
            saved_headers = []
            i = 0
            while i < len(all_headers):
               this_header = all_headers[i]
               if this_header[0].upper() in (header.upper() for header in headers_to_save):
                  saved_headers.append(this_header)
               i += 1
            s3.put_object(Bucket = destination_bucket, Key = key_prefix + "/headers.json", Body = json.dumps(saved_headers))
         
      # parse the mime parts out of the message
      parts = msg.walk()
      
      # walk through each MIME part from the email message
      part_idx = 0
      for part in parts:
         part_idx += 1
         
         # get information about the MIME part
         content_type, content_disposition, content, charset, filename = [None] * 5
         content_type = part.get_content_type()
         content_disposition = str(part.get_content_disposition())
         content = part.get_payload(decode=True)
         if content_type == 'message/rfc822':
            content = part.get_payload(decode=False)[0].as_string()
         charset = part.get_content_charset()
         filename = part.get_filename()
         print(f"Part: {part_idx}. Content charset: {charset}. Content type: {content_type}. Content disposition: {content_disposition}. Filename: {filename}");

         # make file name for body, and untitled text or html parts
         # add additional content types that we want to support non-existent filenames
         if not filename:
            if content_type == 'text/plain':
               if 'attachment' not in content_disposition:
                  filename = "body.txt"
               else:
                  filename = "untitled.txt"
            elif content_type == 'text/html':
               if 'attachment' not in content_disposition:
                  filename = "body.html"
               else:
                  filename = "untitled.html"
            else:
               filename = "untitled"
      
         # TODO: consider overriding or sanitizing the filenames since that is tainted data and might be subject to abuse in object key names
         # technically, the entire message is tainted data, so it would be the responsibility of downstream parsers to ensure protection from interpreter abuse

         # skip parts that aren't attachment parts
         if content_type in ["multipart/mixed", "multipart/related", "multipart/alternative"]:
            continue
         
         if content:
            
            # decode the content based on the character set specified
            # TODO: add error handling
            if charset:
               content = content.decode(charset)
            
            # store the decoded MIME part in S3 with the filename appended to the object key
            s3.put_object(Bucket = destination_bucket, Key = key_prefix + "/mimepart" + str(part_idx) + "_" + filename, Body = content)
            print(content)

            
            if content_type in ["application/gzip", "application/x-gzip"]:
               gz_content = s3.get_object(Bucket=destination_bucket, Key=key_prefix + "/mimepart" + str(part_idx) + "_" + filename)["Body"].read()
               unzipped_content = unzip_gz_content(gz_content)
               gz_key = key_prefix + "/mimepart" + str(part_idx) + "_" + filename
               unzipped_key = gz_key.replace('.gz','')
               s3.put_object(Bucket=destination_bucket, Key=unzipped_key, Body=unzipped_content)
               json_content = xml_to_json(unzipped_content)
               unzipped_json_key = unzipped_key.replace('.xml','.json')
               s3.put_object(Bucket=dmarc_report_bucket, Key = dmarc_report_bucket_folder + "/" + unzipped_json_key, Body=json_content)
            
            if content_type in ["text/xml"]:
               xml_content = s3.get_object(Bucket=destination_bucket, Key=key_prefix + "/mimepart" + str(part_idx) + "_" + filename)["Body"].read()
               xml_key = key_prefix + "/mimepart" + str(part_idx) + "_" + filename
               xml_key = xml_key.replace('.xml','')
               s3.put_object(Bucket=destination_bucket, Key=xml_key, Body=xml_content)
               json_content = xml_to_json(xml_content)
               unzipped_json_key = xml_key.replace('.json','')
               s3.put_object(Bucket=dmarc_report_bucket, Key = dmarc_report_bucket_folder + "/" + unzipped_json_key, Body=json_content)
            
            saved_parts += 1
               
         else:
            print(f"Part {part_idx} has no content. Content type: {content_type}. Content disposition: {content_disposition}.");
      
      if workmail_mutate:
         email_subject = event['subject']
         modified_object_key = key_prefix + "/" + str(uuid.uuid4())
         new_subject =  f"[PROCESSED] {email_subject}"
         msg.replace_header('Subject', new_subject)
         msg.add_header('X-AWS-Mailsploder-Bucket-Prefix', "s3://" + destination_bucket + "/" + key_prefix)
         msg.add_header('X-AWS-Mailsploder-Parts-Saved', str(saved_parts))
         
         # Store updated email in S3
         s3.put_object(Bucket = destination_bucket, Key = modified_object_key, Body = msg.as_bytes())

         # Update the email in WorkMail
         s3_reference = {
            'bucket': destination_bucket,
            'key': modified_object_key
         }
         content = {
            's3Reference': s3_reference
         }
         workmail_message_flow.put_raw_message_content(messageId=message_id, content=content)
   except Exception as e:
      print("Error trapped:", e)
        
   return {
       'statusCode': 200,
       'body': 'Number of parts saved to S3 bucket: ' + destination_bucket + ': ' + str(saved_parts)
   }