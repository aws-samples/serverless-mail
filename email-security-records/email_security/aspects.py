from os.path import exists as file_exists

from aws_cdk import Annotations, IAspect, Stack
import checkdmarc
import jsii

import CONFIG


@jsii.implements(IAspect)
class DmarcChecker:
    def visit(self, node):
        if isinstance(node, Stack):

            # Check DNS records

            domain_results = checkdmarc.check_domains([CONFIG.EMAIL_DOMAIN])

            # MX records

            if domain_results["mx"]["hosts"] == []:
                Annotations.of(node).add_error(
                    f"No MX records for {CONFIG.EMAIL_DOMAIN}."
                )

            # DMARC record

            if domain_results["dmarc"]["record"] is None:
                Annotations.of(node).add_error(
                    f"No DMARC record for {CONFIG.EMAIL_DOMAIN}."
                )
            elif not domain_results["dmarc"]["valid"]:
                Annotations.of(node).add_error(
                    f"DMARC record for {CONFIG.EMAIL_DOMAIN} is invalid."
                )
            elif domain_results["dmarc"]["tags"]["p"]["value"] not in [
                "quarantine",
                "reject",
            ]:
                Annotations.of(node).add_error(
                    f'BIMI requires a DMARC domain policy of either "quarantine" or "reject".'
                )
            elif domain_results["dmarc"]["tags"]["sp"]["value"] not in [
                "quarantine",
                "reject",
            ]:
                Annotations.of(node).add_error(
                    f'BIMI requires a DMARC subdomain policy of either "quarantine" or "reject".'
                )
            else:
                Annotations.of(node).add_info(
                    f"DMARC record for {CONFIG.EMAIL_DOMAIN} is valid for BIMI."
                )

            # MTA-STS policy file

            mta_sts_file_path = "assets/.well-known/mta-sts.txt"

            if not file_exists(mta_sts_file_path):
                Annotations.of(node).add_error(
                    f"MTA-STS policy file not found at {mta_sts_file_path}."
                )
