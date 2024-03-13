from aws_cdk import NestedStack


class pyNestedClass(NestedStack):
    """This class is a small wrapper for cdk NestedStack
    preventing passing unexpected parameter  env  from **kwargs to NestedStack constructor."""

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **{p: kwargs[p] for p in kwargs.keys() if p not in ['env']})
