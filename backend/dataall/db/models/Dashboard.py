from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import query_expression

from .. import Base, Resource, utils


class Dashboard(Resource, Base):
    __tablename__ = 'dashboard'
    environmentUri = Column(String, ForeignKey("environment.environmentUri"), nullable=False)
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

    def uri(self):
        return self.dashboardUri
