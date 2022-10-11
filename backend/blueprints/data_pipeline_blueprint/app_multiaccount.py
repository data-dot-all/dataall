#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ddk_app.ddk_app_stack import DdkApplicationStack

from utils.config import MultiaccountConfig

stage_id = os.environ.get('STAGE', None)
pipeline_name = os.environ.get('PIPELINE_NAME')

app = cdk.App()

config = MultiaccountConfig()
environment_id = config.get_stage_env_id(stage_id)
env_vars = config.get_env_var_config(environment_id)


DdkApplicationStack(app,
                    f"{pipeline_name}-DdkApplicationStack",
                    environment_id,
                    env_vars)

app.synth()
