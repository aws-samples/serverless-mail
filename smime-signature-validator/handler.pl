#!/usr/bin/env perl

# install dependencies with:
# docker run --rm -v $PWD:/var/task shogo82148/p5-aws-lambda:build-5.34-paws.al2 cpanm --verbose --notest --local-lib extlocal --no-man-pages --installdeps .
use lib 'extlocal/lib/perl5';
use Crypt::SMIME;
use Crypt::OpenSSL::X509;
use Paws; $ENV{PAWS_SILENCE_UNSTABLE_WARNINGS} = 1; # we're just using Paws to get and put objects
use JSON;
use strict;
use warnings;

# the Lambda function handler
# test locally using:
# docker run --rm -v $PWD:/var/task -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN shogo82148/p5-aws-lambda:5.34-paws.al2 handler.handle '{"bucket":"examplebucket","key":"example.eml"}'
sub handle {
    my ($payload, $context) = @_;
    my $s3_bucket = $payload->{bucket};
    my $s3_object_key = $payload->{key};
    
    # get the email message from the S3 bucket
    my $email = get_s3_object($s3_bucket, $s3_object_key);
    
    # get S/MIME results for this message
    my $smime_result = get_smime_result($email);
    
    if ( $ENV{SAVE_TO_BUCKET} and $ENV{SAVE_TO_BUCKET} =~ /true/i ) {
        if ( put_s3_object($s3_bucket, $s3_object_key.".smime.json", $smime_result) ) {
            warn "saved smime results to s3://$s3_bucket/$s3_object_key.smime.json\n";
        }
        else {
            warn "unable to save smime results to bucket\n";
        }
    }
    
    # return the results back to the function caller
    return $smime_result;
}

sub get_smime_result {
    my $signed_mime = shift;
    my $smime = Crypt::SMIME->new();
    my %result = ();
    
    # is the message even signed
    $result{signed} = ($smime->isSigned($signed_mime) ? "true" : "false");
    $result{encrypted} = ($smime->isEncrypted($signed_mime) ? "true" : "false");
    return \%result if ( $result{signed} ne 'true' );
    
    # check the S/MIME signature to see if it looks parsable
    eval{ return $smime->check($signed_mime, Crypt::SMIME::NO_CHECK_CERTIFICATE) };
    $result{check} = $@ ? $@ : "ok";
    return \%result if ( $result{check} ne 'ok' );
    
    # check the S/MIME signature chain
    # CA certificates stored in S3 and managed by you - whomever you choose to trust
    if ( ! -e '/tmp/keystore' and $ENV{CACERT_BUCKET} and $ENV{CACERT_KEY} ) {
        my $cacert = get_s3_object($ENV{CACERT_BUCKET}, $ENV{CACERT_KEY});
        if ( $cacert ) {
            open my $fh, '>', '/tmp/keystore' or die $!;
            print $fh $cacert;
            close $fh;
            warn "Loaded CA keystore from s3://$ENV{CACERT_BUCKET}/$ENV{CACERT_KEY}\n";
        }
    }
    if ( -e '/tmp/keystore' ) {
        eval { $smime->setPublicKeyStore('/tmp/keystore') };
        if ( $@ ) {
            warn "failed to setPublicKeyStore: $@\n";
        }
    }
    else {
        warn "No CA keystore available\n";
    }
    eval{ return $smime->check($signed_mime) };
    $result{check_chain} = $@ ? $@ : "ok";
    
    # get the S/MIME signer details
    my @signers = eval { @{Crypt::SMIME::getSigners($signed_mime)} };
    unless ( $@ ) {
        for ( @signers ) {
            my $i = 0;
            my $x509 = Crypt::OpenSSL::X509->new_from_string($_);
            for my $attribute ( qw(pubkey subject hash email issuer issuer_hash notBefore notAfter modulus exponent fingerprint_md5 fingerprint_sha256 as_string) ) {
                $result{signers}[$i]{$attribute} = $x509->$attribute();
            }
            $i++;
        }
    }
    
    # return the S/MIME details collected
    return \%result;
}

sub get_s3_object {
    my ($bucket, $key) = @_;
    my $s3 = Paws->service('S3', region => 'us-east-1');
    my $res = $s3->GetObject(
        Bucket => $bucket,
        Key => $key,
    );
    return $res->Body;
}

sub put_s3_object {
    my ($bucket, $key, $data) = @_;
    my $s3 = Paws->service('S3', region => 'us-east-1');
    my $res = eval { $s3->PutObject(
        Bucket => $bucket,
        Key => $key,
        Body => encode_json($data)
    )};
    if ( $@ ) {
        warn $@;
        return undef;
    }
    return 1;
}

1;