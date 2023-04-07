"""The package defines the schema for Omics Pipelines"""

from dataall.modules.omics.api import input_types, mutations, queries, schema, resolvers

__all__ = ["schema", "input_types", "queries", "mutations", "resolvers"]
