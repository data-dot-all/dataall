import textwrap

from ._cache import cache_instances


@cache_instances
class InputType:
    def __init__(self, name, arguments, description=''):
        self.name = name
        self.arguments = arguments
        self.description = description

    def gql(self):
        n = '\n'
        description_str = f'"""{self.description}"""{n}' if self.description else ''

        # args = f"{', '.join([arg.name+':'+ arg.type.gql() for arg in self.arguments])}"
        args = f'{", ".join([arg.gql() for arg in self.arguments])}'
        return description_str + n.join(textwrap.wrap(f'input {self.name}{{{n} {args} }}'))
