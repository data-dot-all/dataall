from dataall.base.api import GraphQLEnumMapper


# Enums used for dataset expiration.
# Could be repurposed for environment, worksheet, etc if need be
# This is defined here instead of the dataset_enums file because this is used in common_module_utils.py
class Expiration(GraphQLEnumMapper):
    Monthly = 'Monthly'
    Quartely = 'Quarterly'
