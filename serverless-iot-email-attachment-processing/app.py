#!/usr/bin/env python3

import aws_cdk as cdk

from stack import SesStack

app = cdk.App()
stack = SesStack(app, "SesStack")

app.synth()
