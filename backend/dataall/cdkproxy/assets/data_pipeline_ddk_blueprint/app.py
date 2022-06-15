#!/usr/bin/env python3
import os

import aws_cdk as cdk
from ddk_app.ddk_app_stack import DdkApplicationStack

app = cdk.App()
pipeline_name = os.environ.get('PIPELINE_NAME')
DdkApplicationStack(app, f"{pipeline_name}-DdkApplicationStack", "dev")

app.synth()
