from sqlalchemy import Column, String, DateTime, ARRAY

from .. import Base
from .. import Resource, utils
import datetime
from sqlalchemy.dialects import postgresql


class LFTagPermissions(Base):
    __tablename__ = 'lftagpermissions'
    tagPermissionUri = Column(String, primary_key=True, default=utils.uuid('lftag'))
    SamlGroupName = Column(String, nullable=False)
    environmentUri = Column(String, nullable=False)
    environmentLabel = Column(String, nullable=False)
    awsAccount = Column(String, nullable=False)
    tagKey = Column(String, nullable=False)
    tagValues = Column(ARRAY(String))
