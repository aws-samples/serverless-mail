from aws_cdk import Annotations, IAspect, Stack
import checkdmarc
import jsii

import CONFIG


@jsii.implements(IAspect)
class DmarcChecker:
    def visit(self, node):
        if isinstance(node, Stack):
            domain_results = checkdmarc.check_domains([CONFIG.EMAIL_DOMAIN])

            if not domain_results["dmarc"]["valid"]:
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
