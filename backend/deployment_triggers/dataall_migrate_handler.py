import logging
import os

from migrations.dataall_migrations.herder import Herder

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

class BaseC:
    name = "base"
    @classmethod
    def test(cls):
        print(cls.name)


class A(BaseC):
    name = "class A"

class B(BaseC):
    name = "class B"
    @classmethod
    def test(cls):
        print(cls.name)


def handler(event, context) -> None:
    #H = Herder()
    #H.upgrade()
    A.test()
    B.test()
