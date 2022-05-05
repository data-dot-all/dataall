from sqlalchemy import ARRAY, Boolean, Column, Integer, String
from sqlalchemy.orm import query_expression

from .. import Base, Resource, utils


class RedshiftCluster(Resource, Base):
    __tablename__ = "redshiftcluster"
    environmentUri = Column(String, nullable=False)
    organizationUri = Column(String, nullable=False)
    clusterUri = Column(String, primary_key=True, default=utils.uuid("cluster"))
    clusterArn = Column(String)
    clusterName = Column(String)
    description = Column(String)
    databaseName = Column(String, default="datahubdb")
    databaseUser = Column(String, default="datahubuser")
    masterUsername = Column(String)
    masterDatabaseName = Column(String)
    nodeType = Column(String)
    numberOfNodes = Column(Integer)
    region = Column(String, default="eu-west-1")
    AwsAccountId = Column(String)
    kmsAlias = Column(String)
    status = Column(String, default="CREATING")
    vpc = Column(String)
    subnetGroupName = Column(String)
    subnetIds = Column(ARRAY(String), default=[])
    securityGroupIds = Column(ARRAY(String), default=[])
    CFNStackName = Column(String)
    CFNStackStatus = Column(String)
    CFNStackArn = Column(String)
    IAMRoles = Column(ARRAY(String), default=[])
    endpoint = Column(String)
    port = Column(Integer)
    datahubSecret = Column(String)
    masterSecret = Column(String)
    external_schema_created = Column(Boolean, default=False)
    SamlGroupName = Column(String)
    imported = Column(Boolean, default=False)
    userRoleForCluster = query_expression()
    userRoleInEnvironment = query_expression()
