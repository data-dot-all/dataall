from dataall.db import DbConfig


def test_sanitize_database():
    config = DbConfig(
        user='dataall',
        pwd='123456789',
        host="dataall.eu-west-1.rds.amazonaws.com",
        db='dataall\'; DROP TABLE users;',
        schema='dev'
    )

    # connection injection: 'postgresql+pygresql://dataall:123456789@dataall.eu-west-1.rds.amazonaws.com/dataall'; DROP TABLE users;
    assert config.url == \
           'postgresql+pygresql://dataall:123456789@dataall.eu-west-1.rds.amazonaws.com/dataallDROPTABLEusers'


def test_sanitize_user():
    config = DbConfig(
        user='dataall2;^&*end',
        pwd='qwsufn3i20d-_s3qaSW3d2',
        host="dataall.eu-west-1.rds.amazonaws.com",
        db='dataall',
        schema='dev'
    )

    assert config.url == \
           'postgresql+pygresql://dataall2end:qwsufn3i20d-_s3qaSW3d2@dataall.eu-west-1.rds.amazonaws.com/dataall'


def test_sanitize_pwd():
    config = DbConfig(
        user='dataall',
        pwd='qazxsVFRTGBdfrew-332_c2@dataall.eu-west-1.rds.amazonaws.com/dataall\'; drop table dataset; # ',
        host="dataall.eu-west-1.rds.amazonaws.com",
        db='dataall',
        schema='dev'
    )

    # without sanitation should be :
    # postgresql+pygresql://dataall:qazxsVFRTGBdfrew-332_c2@dataall.eu-west-1.rds.amazonaws.com/dataall'
    # drop table dataset; # @dataall.eu-west-1.rds.amazonaws.com/dataall
    assert config.url == \
           "postgresql+pygresql://dataall:qazxsVFRTGBdfrew-332_c2@dataall.eu-west-1.rds.amazonaws.com" \
           "dataalldroptabledataset@dataall.eu-west-1.rds.amazonaws.com/dataall"


def test_sanitize_host():
    config = DbConfig(
        user='dataall',
        pwd='q68rjdmwiosoxahGDYJWIdi-9eu93_9dJJ_',
        host="dataall.eu-west-1$%#&@*#)$#.rds.amazonaws.com",
        db='dataall',
        schema='dev'
    )

    assert config.url == "postgresql+pygresql://dataall:q68rjdmwiosoxahGDYJWIdi-9eu93_9dJJ_@dataall.eu-west-1.rds.amazonaws.com/dataall"
