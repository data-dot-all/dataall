from dataall.base.api import GraphQLEnumMapper


class PolicyManagementOptions(GraphQLEnumMapper):
    FULLY_MANAGED = 'Fully-Managed'
    PARTIALLY_MANAGED = 'Partially-Managed'
    EXTERNALLY_MANAGED = 'Externally-Managed'


