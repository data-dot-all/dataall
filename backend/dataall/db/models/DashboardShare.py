from enum import Enum

from sqlalchemy import Column, String

from .. import Base, utils


class DashboardShareStatus(Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DashboardShare(Base):
    __tablename__ = "dashboardshare"
    shareUri = Column(String, nullable=False, primary_key=True, default=utils.uuid("shareddashboard"))
    dashboardUri = Column(String, nullable=False, default=utils.uuid("dashboard"))
    SamlGroupName = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    status = Column(String, nullable=False, default=DashboardShareStatus.REQUESTED.value)
