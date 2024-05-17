from ariadne import (
    gql,
)
from graphql import print_schema, print_introspection_schema, introspection_from_schema
from dataall.base.api import bootstrap as bootstrap_schema, get_executable_schema
from dataall.base.loader import load_modules, ImportMode
import json 
load_modules(ImportMode.all())

SCHEMA = bootstrap_schema()
TYPE_DEFS = gql(SCHEMA.gql(with_directives=False))
executable_schema = get_executable_schema()

with open("test.json", "x") as f:
    f.write(json.dumps(introspection_from_schema(executable_schema)))