import textwrap

class InputType:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

    def gql(self):
        n = '\n'
        # args = f"{', '.join([arg.name+':'+ arg.type.gql() for arg in self.arguments])}"
        args = f"{', '.join([arg.gql() for arg in self.arguments])}"
        return '\n'.join(textwrap.wrap(f'input {self.name}{{{n} {args} }}'))
