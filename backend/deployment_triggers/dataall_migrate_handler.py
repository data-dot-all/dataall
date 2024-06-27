import logging
import os
import platform
from migrations.dataall_migrations.herder import Herder

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

class BaseC:
    name = "base"
    @classmethod
    def test(cls):
        print("test")
        print("Classname: ", cls.__name__)
        print("Attribute value: ", cls.name)

        print("All attributes: ", cls.__dict__)


class A(BaseC):
    name = "class A"

class B(BaseC):
    name = "class B"
    @classmethod
    def test(cls):
        print("test")
        print("Classname: ", cls.__name__)
        print("Attribute value: ", cls.name)

        print("All attributes: ", cls.__dict__)

def handler(event, context) -> None:
    #H = Herder()
    #H.upgrade()
    print("Python version = ", platform.python_version())
    print("Python compiler = ", platform.python_compiler())
    print("Python release = ", platform.release())
    print("Python platform = ", platform.platform())

    BaseC.test()
    A.test()
    B.test()

