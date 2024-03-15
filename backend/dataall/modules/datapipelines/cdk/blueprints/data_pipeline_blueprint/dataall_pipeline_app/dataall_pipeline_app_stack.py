from typing import Any, Optional

from aws_cdk import Environment
from aws_ddk_core import BaseStack, Configurator
from constructs import Construct


class DataallPipelineStack(BaseStack):
    def __init__(
        self, scope: Construct, id: str, environment_id: str, env: Optional[Environment] = None, **kwargs: Any
    ) -> None:
        super().__init__(
            scope,
            id,
            environment_id=environment_id,
            env=env or Configurator.get_environment(config_path='./ddk.json', environment_id=environment_id),
            **kwargs,
        )
        Configurator(scope=self, config='./ddk.json', environment_id=environment_id)

        # The code that defines your stack goes here:
