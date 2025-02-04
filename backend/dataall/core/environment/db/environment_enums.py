from dataall.base.api import GraphQLEnumMapper


class ConsumptionRolePolicyManagementOptions(GraphQLEnumMapper):
    FULLY_MANAGED = 'FullyManaged'
    PARTIALLY_MANAGED = 'PartiallyManaged'
    EXTERNALLY_MANAGED = 'ExternallyManaged'
