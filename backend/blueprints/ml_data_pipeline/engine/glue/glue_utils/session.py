from glue_config_reader import ConfigReader
from runner import Runner


class A:
    def __init__(self, **config):
        self.__dict__.update(config)

    def run_step(self):
        print('A.run_step')


def wrapper(name):
    def decorator(cls):
        class Decorated(cls, A):
            X = 'xxxx'

            def __init__(self, **config):
                super().__init__(**config)

        return Decorated

    return decorator


@wrapper(name='Xsss')
class B:
    def run_step(self):
        print('B.run_step')


class Rdd:
    def __init__(self):
        pass

    def countApprox(self):
        return 2345


class Dataframe:
    def __init__(self, *args, **kwargs):
        self.write = Writer()
        self.rdd = Rdd()

    def show(self, n=10):
        pass

    def createOrReplaceTempView(self, name):
        pass


class Writer:
    def __init__(self, *args, **kwargs):
        pass

    def mode(self, *args, **kwargs):
        return self

    def format(self, *args, **kwargs):
        return self

    def option(self, *args, **kwargs):
        return self

    def saveAsTable(self, *args, **kwargs):
        print(args[0])
        return self


class Reader:
    def __init__(self, *args, **kwargs):
        pass

    def load(self, *args, **kwargs):
        return Dataframe()


class Spark:
    def __init__(self):
        self.read = Reader()

    def sql(self, query):
        return Dataframe()


config = ConfigReader('config.yaml')
session = Runner(config=config, spark=Spark())

session.run()
