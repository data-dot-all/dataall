class Context:
    def __init__(
        self,
        engine=None,
        username=None,
        groups=None,
    ):
        self.engine = engine
        self.username = username
        self.groups = groups
