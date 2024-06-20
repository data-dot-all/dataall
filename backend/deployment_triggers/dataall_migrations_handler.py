from migrations.dataall_migrations.herder import Herder


def handler():
    H = Herder()
    H.upgrade()