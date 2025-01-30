class DirectiveArgs:
    def __init__(self, name, **kwargs):
        self.name = name
        self.args = kwargs

    @staticmethod
    def to_string(literal):
        if isinstance(literal, str):
            return f'"{literal}"'
        elif isinstance(literal, bool):
            return f'{"true" if literal else "false"}'
        elif getattr(literal, '__call__', None):
            return f'"{literal.__name__}"'
        else:
            return f'{str(literal)}'

    def gql(self, with_directives=True):
        if not len(self.args.keys()):
            return f'@{self.name}'
        else:
            return (
                f'@{self.name}({",".join([k + ":" + DirectiveArgs.to_string(self.args[k]) for k in self.args.keys()])})'
            )


if __name__ == '__main__':
    uri = DirectiveArgs(name='uri', model='X', param=2, bool=True)
    print(uri.gql())
