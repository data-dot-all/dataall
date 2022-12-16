def cache_instances(cls):
    class X(cls):
        class_instances = {}

        def __init__(self, name, scope='default', *args, **kwargs):
            super().__init__(name, *args, **kwargs)
            self.scope = scope
            print(f"init X, name={name}")
            if not X.class_instances.get(scope):
                X.class_instances[scope] = {}
                print(f"scope={scope}")
            X.class_instances[scope][name] = self

        @classmethod
        def get_instance(cls, name, scope='default'):
            print("initializing class instances. Inside class method of class X")
            return cls.class_instances[scope].get(name, None)

    return X
