from enum import Enum as PythonEnum

from ._cache import cache_instances


@cache_instances
class GraphqlEnum:
    def __init__(self, name, values: PythonEnum = None):
        self.name = name
        self.values = values

    def gql(self, with_directives=True):
        n = '\n'
        # return f"enum {self.name}{{{n}{n.join(self.values)}{n}}}"
        return f'enum {self.name}{{{n}{n.join([v.name for v in self.values])}{n}}}'


if __name__ == '__main__':

    class Day(PythonEnum):
        monday = '01'
        tuesday = '02'

    episode = GraphqlEnum(name='Episode', values=Day)

    print(episode.gql())
