"""The package defines the schema for Maintenance Module"""

from dataall.modules.maintenance.api import mutations, queries, types, resolvers, enums

__all__ = ['types', 'queries', 'mutations', 'resolvers', 'enums']
