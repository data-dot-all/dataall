from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import query_expression

from .. import Base, Resource, utils


class Vpc(Resource, Base):
    __tablename__ = 'vpc'
    environmentUri = Column(String, nullable=False)
    vpcUri = Column(
        String, nullable=False, primary_key=True, default=utils.uuid('vpcUri')
    )
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    SamlGroupName = Column(String)
    VpcId = Column(String, nullable=False)
    privateSubnetIds = Column(ARRAY(String))
    publicSubnetIds = Column(ARRAY(String))
    default = Column(Boolean, default=False)
    userRoleForPipeline = query_expression()
