# Deployment environment
# ACCOUNT is the AWS account number to deploy this solution
ACCOUNT = ""
# REGION - e.g. us-east-1
REGION = ""

# DNS
EMAIL_DOMAIN = ""
ROUTE_53_HOSTED = True

# Existing ACM TLS certificate for CloudFront
TLS_CERTIFICATE_ARN = None

# Subdomain where BIMI assets will be hosted
BIMI_ASSETS_SUBDOMAIN = "bimi-assets"

# Filenames for logo and verified mark certificate
LOGO_FILENAME = "logo.svg"
VMC_FILENAME = "bimi_vmc.pem"

# MTA-STS config
MTA_STS_ID = "202203311405"
MTS_STS_MODE = "testing"

# TLSRPT Addresses
# The email address that should receive TLS reports
TLSRPT_ADDRESSES = [""]
