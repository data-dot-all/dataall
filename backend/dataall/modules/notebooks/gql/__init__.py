"""The package defines the schema for SageMaker notebooks"""
from dataall.modules.notebooks.gql import input_types, mutations, queries, types, resolvers

__all__ = ["types", "input_types", "queries", "mutations", "resolvers"]
