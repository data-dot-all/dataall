import os

from dataall.db.connection import (ENVNAME, create_schema_if_not_exists,
                                   drop_schema_if_exists, get_engine)

if __name__ == "__main__":
    engine = get_engine(envname=ENVNAME).engine
    schema = os.getenv("schema_name", ENVNAME)
    print(f"Dropping schema {schema}...")
    drop_schema_if_exists(get_engine(envname=ENVNAME).engine, envname=schema)
    create_schema_if_not_exists(get_engine(envname=ENVNAME).engine, envname=schema)
    print(f"Clean schema {schema} recreated")
