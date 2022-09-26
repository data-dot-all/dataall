from typing import Any

from aws_ddk_core.base import BaseStack
from aws_ddk_core.resources import S3Factory
from constructs import Construct


class DdkApplicationStack(BaseStack):

    def __init__(self, scope: Construct, id: str, environment_id: str, **kwargs: Any) -> None:
        super().__init__(scope, id, environment_id, **kwargs)

        # The code that defines your stack goes here:

