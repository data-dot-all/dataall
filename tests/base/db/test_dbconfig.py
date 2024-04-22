import pytest

from dataall.base.db import DbConfig


def test_incorrect_database():
    with pytest.raises(ValueError):
        DbConfig(
            user='dataall',
            pwd='123456789',
            host='dataall.eu-west-1.rds.amazonaws.com',
            db="dataall'; DROP TABLE users;",
            schema='dev',
        )


def test_incorrect_user():
    with pytest.raises(ValueError):
        DbConfig(
            user='dataall2;^&*end',
            pwd='qwsufn3i20d-_s3qaSW3d2',
            host='dataall.eu-west-1.rds.amazonaws.com',
            db='dataall',
            schema='dev',
        )


def test_incorrect_pwd():
    with pytest.raises(ValueError):
        DbConfig(
            user='dataall',
            pwd="qazxsVFRTGBdfrew-332_c2@dataall.eu-west-1.rds.amazonaws.com/dataall'; drop table dataset; # ",
            host='dataall.eu-west-1.rds.amazonaws.com',
            db='dataall',
            schema='dev',
        )


def test_incorrect_host():
    with pytest.raises(ValueError):
        DbConfig(
            user='dataall',
            pwd='q68rjdmwiosoxahGDYJWIdi-9eu93_9dJJ_',
            host='dataall.eu-west-1$%#&@*#)$#.rds.amazonaws.com',
            db='dataall',
            schema='dev',
        )


def test_correct_config():
    # no exception is raised
    DbConfig(user='dataall', pwd='q68rjdm_aX', host='dataall.eu-west-1.rds.amazonaws.com', db='dataall', schema='dev')
