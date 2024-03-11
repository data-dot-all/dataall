from typing import Callable

from awscdk.appsync_utils import GraphqlType, Type


class ThunkField(GraphqlType):
    def __init__(self, func: Callable[[], GraphqlType]):
        super().__init__(Type.INTERMEDIATE)
        self.func = func

    def to_string(self) -> str:
        return self.func().to_string()

    def args_to_string(self) -> str:
        return self.func().args_to_string()

    def directives_to_string(self, modes=None) -> str:
        return self.func().directives_to_string(modes)
