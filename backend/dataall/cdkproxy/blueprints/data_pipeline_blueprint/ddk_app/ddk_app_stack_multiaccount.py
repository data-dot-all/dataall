from typing import Any, Optional

from aws_cdk import Environment, Tags
from aws_ddk_core.base import BaseStack
from aws_ddk_core.config import Config
from constructs import Construct


class DdkApplicationStack(BaseStack):


    def __init__(self, scope: Construct,
                 id: str,
                 environment_id: str,
                 env_vars: dict,
                 env: Optional[Environment] = None,
                 **kwargs: Any) -> None:
        self._config = Config()
        super().__init__(
            scope,
            id,
            environment_id=environment_id,
            env=env or self._config.get_env(environment_id),
            **kwargs)

        Tags.of(self).add("Team", str(env_vars['Team']))

        # The code that defines your stack goes here:
