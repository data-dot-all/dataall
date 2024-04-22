class Thunk:
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args or []
        self.kwargs = kwargs or {}

    @property
    def target(self):
        return self.fn(*self.args, **self.kwargs)

    def gql(self):
        return self.target.gql()


if __name__ == '__main__':
    from ..gql import Field
    from ..gql import String

    Foo = Field(name='foo', type=String)
    t = Thunk(lambda: Foo)
    print(t.target.gql())

    print(isinstance(t, Thunk))
