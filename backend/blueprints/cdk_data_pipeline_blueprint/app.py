
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
        super().__init__(scope, f"dataall-{environment_id.title()}", **kwargs)
        DDKApplicationStack(self, "DataPipeline-reina1-yg0jvyp9", environment_id)

config = Config()
(
    CICDPipelineStack(
        app,
        id="dataall-pipeline-reina1-yg0jvyp9",
        environment_id="cicd",
        pipeline_name="reina1",
    )
        .add_source_action(repository_name="dataall-reina1-yg0jvyp9")
        .add_synth_action()
        .build().add_stage("dev", ApplicationStage(app, "dev", env=config.get_env("dev"))).add_stage("prod", ApplicationStage(app, "prod", env=config.get_env("prod")))
        .synth()
)

app.synth()

