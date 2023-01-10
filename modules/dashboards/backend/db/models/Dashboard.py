from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression
from enum import Enum

from backend.db import Base, Resource, utils

class DashboardRole(Enum):
    Creator = '999'
    Admin = '900'
    Shared = '800'
    NoPermission = '000'


class Dashboard(Resource, Base):
    __tablename__ = 'dashboard'
    environmentUri = Column(String, nullable=False)
    organizationUri = Column(String, nullable=False)
    dashboardUri = Column(
        String, nullable=False, primary_key=True, default=utils.uuid('dashboard')
    )
    region = Column(String, default='eu-west-1')
    AwsAccountId = Column(String, nullable=False)
    namespace = Column(String, nullable=False)
    DashboardId = Column(String, nullable=False)
    SamlGroupName = Column(String, nullable=False)

    userRoleForDashboard = query_expression()
