from dataall.base.api.constants import GraphQLEnumMapper


class WarehouseType(GraphQLEnumMapper):
    RedshiftServerless = 'RedshiftServerless'
    RedshiftCluster = 'RedshiftCluster'


class AuthenticationType(GraphQLEnumMapper):
    IAMFederation = 'IAMFederation'
    SecretsManager = 'SecretsManager'


class ConsumerType(GraphQLEnumMapper):
    RedshiftRole = 'RedshiftRole'
    RedshiftWarehouse = 'RedshiftWarehouse'
