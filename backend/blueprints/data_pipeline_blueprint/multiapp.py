#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_ddk_core.config.config import Config
from ddk_app.ddk_app_stack import DdkApplicationStack

stage_id = os.environ.get('STAGE', None)
pipeline_name = os.environ.get('PIPELINE_NAME')

app = cdk.App()

config = Config()
environment = config.get_env(stage_id)

if not environment:
    raise ValueError(f'Environment id with stage_id {stage_id} was not found!')

# We can also add environment variables, read them and pass them to the stack
# env_config = config.get_env_config(stage_id)

DdkApplicationStack(app,
                    f"{pipeline_name}-DdkApplicationStack",
                    stage_id)

app.synth()
