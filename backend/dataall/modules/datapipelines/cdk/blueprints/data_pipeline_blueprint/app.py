#!/usr/bin/env python3
import os
import aws_cdk as cdk
from dataall_pipeline_app.dataall_pipeline_app_stack import DataallPipelineStack

environment_id = os.environ.get('STAGE', 'dev')
pipeline_name = os.environ.get('PIPELINE_NAME', 'dataall-pipeline-stack')

app = cdk.App()

DataallPipelineStack(app, f'{pipeline_name}-{environment_id}-DataallPipelineStack', environment_id)

app.synth()
