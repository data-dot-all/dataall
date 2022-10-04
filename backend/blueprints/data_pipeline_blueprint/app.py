
# !/usr/bin/env python3

import aws_cdk as cdk
from aws_ddk_core.cicd import CICDPipelineStack
from ddk_app.ddk_app_stack import DDKApplicationStack
from aws_ddk_core.config import Config

app = cdk.App()

class ApplicationStage(cdk.Stage):
    def __init__(
            self,
            scope,
            environment_id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, f"mo1-{environment_id.title()}", **kwargs)
        DDKApplicationStack(self, "DataPipeline-mo1", environment_id)

config = Config()
(
    CICDPipelineStack(
        app,
        id="dataall-pipelinepip-zpde4bd0pip",
        environment_id="cicd",
        pipeline_name="mo1",
    )
        .add_source_action(repository_name="dataall-mo1-zpde4bd0")
        .add_synth_action()
        .build().add_stage("dev", ApplicationStage(app, "dev", env=config.get_env("dev")))
        .synth()
)

app.synth()

