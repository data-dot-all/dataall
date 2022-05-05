import os

import dataall


def test(db: dataall.db.Engine):
    if os.getenv("local") or os.getenv("pytest"):
        config: dataall.db.DbConfig = db.dbconfig
        print(config)
        assert config.params.get("host") == "localhost"
        assert config.params.get("port") == "5432"
        assert config.params.get("schema") == "pytest"
        with db.scoped_session() as session:
            models = []
            models = models + dataall.db.Base.__subclasses__()
            models = models + dataall.db.Resource.__subclasses__()
            for model in models:
                nb = session.query(model).count()
                assert nb == 0
    else:
        assert True
