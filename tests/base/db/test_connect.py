import os
import dataall


def test(db: dataall.base.db.Engine):
    if os.getenv('local') or os.getenv('pytest'):
        config: dataall.base.db.DbConfig = db.dbconfig
        print(config)
        assert config.host == 'localhost'
        assert config.schema == 'pytest'
        with db.scoped_session() as session:
            models = []
            models = models + dataall.base.db.Base.__subclasses__()
            models = models + dataall.base.db.Resource.__subclasses__()
            for model in models:
                nb = session.query(model).count()
                assert nb == 0
    else:
        assert True
