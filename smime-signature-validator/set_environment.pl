#!/usr/bin/env perl
my @creds = `cat ~/.aws/credentials`;
for (@creds) {
    my ($to_export_key, $to_export_value) = $_ =~ /(aws_access_key_id|aws_secret_access_key|aws_session_token)=(.*)/;
    next unless $to_export_key and $to_export_value;
    $to_export_key = uc($to_export_key);
    print "export $to_export_key=$to_export_value\n";
}