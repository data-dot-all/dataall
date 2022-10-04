from typing import Any

from aws_ddk_core.base import BaseStack
from constructs import Construct


class DDKApplicationStack(BaseStack):

    def __init__(self, scope: Construct, id: str, environment_id: str, **kwargs: Any) -> None:
        super().__init__(scope, id, environment_id, **kwargs)

        # The code that defines your stack goes here:
