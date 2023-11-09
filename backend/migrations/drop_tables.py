import os

from dataall.base.db.connection import (
    ENVNAME,
    get_engine,
    drop_schema_if_exists,
    create_schema_if_not_exists,
)

if __name__ == '__main__':
    engine = get_engine(envname=ENVNAME).engine
    print(f'Dropping schema {ENVNAME}...')
    drop_schema_if_exists(get_engine(envname=ENVNAME).engine, envname=ENVNAME)
    create_schema_if_not_exists(get_engine(envname=ENVNAME).engine, envname=ENVNAME)
    print(f'Clean schema {ENVNAME} recreated')
