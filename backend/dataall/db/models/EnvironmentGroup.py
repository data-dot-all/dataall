import datetime

from sqlalchemy import Column, DateTime, String, Boolean

from .Enums import EnvironmentPermission as EnvironmentPermissionEnum
from .. import Base


class EnvironmentGroup(Base):
    __tablename__ = "environment_group_permission"
    groupUri = Column(String, primary_key=True)
    environmentUri = Column(String, primary_key=True)
    invitedBy = Column(String, nullable=True)
    environmentIAMRoleArn = Column(String, nullable=True)
    environmentIAMRoleName = Column(String, nullable=True)
    environmentIAMRoleImported = Column(Boolean, default=False)
    environmentAthenaWorkGroup = Column(String, nullable=True)
    description = Column(String, default="No description provided")
    created = Column(DateTime, default=datetime.datetime.now)
    updated = Column(DateTime, onupdate=datetime.datetime.now)
    deleted = Column(DateTime)

    # environmentRole is the role of the entity (group or user) in the Environment
    groupRoleInEnvironment = Column(String, nullable=False, default=EnvironmentPermissionEnum.Invited.value)
