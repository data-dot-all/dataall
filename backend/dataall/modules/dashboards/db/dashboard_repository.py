import logging

from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.base.db import exceptions, paginate
from dataall.modules.dashboards.db.models import DashboardShare, DashboardShareStatus, Dashboard

logger = logging.getLogger(__name__)


class DashboardRepository(EnvironmentResource):

    @staticmethod
    def count_resources(session, environment, group_uri) -> int:
        return (
            session.query(Dashboard)
            .filter(
                and_(
                    Dashboard.environmentUri == environment.environmentUri,
                    Dashboard.SamlGroupName == group_uri
                ))
            .count()
        )

    @staticmethod
    def update_env(session, environment):
        return EnvironmentService.get_boolean_env_param(session, environment, "dashboardsEnabled")

    @staticmethod
    def create_dashboard(session, env, username: str, data) -> Dashboard:
        dashboard: Dashboard = Dashboard(
            label=data.label,
            environmentUri=data.environmentUri,
            organizationUri=env.organizationUri,
            region=env.region,
            DashboardId=data.dashboardId,
            AwsAccountId=env.AwsAccountId,
            owner=username,
            namespace='test',
            tags=data.tags,
            SamlGroupName=data.SamlGroupName,
            description=data.description
        )
        session.add(dashboard)
        session.commit()
        return dashboard

    @staticmethod
    def get_dashboard_by_uri(session, uri) -> Dashboard:
        dashboard: Dashboard = session.query(Dashboard).get(uri)
        if not dashboard:
            raise exceptions.ObjectNotFound('Dashboard', uri)
        return dashboard

    @staticmethod
    def _query_user_dashboards(session, username, groups, filter) -> Query:
        query = (
            session.query(Dashboard)
            .outerjoin(
                DashboardShare,
                Dashboard.dashboardUri == DashboardShare.dashboardUri,
            )
            .filter(
                or_(
                    Dashboard.owner == username,
                    Dashboard.SamlGroupName.in_(groups),
                    and_(
                        DashboardShare.SamlGroupName.in_(groups),
                        DashboardShare.status
                        == DashboardShareStatus.APPROVED.value,
                    ),
                )
            )
        )
        if filter and filter.term:
            query = query.filter(
                or_(
                    Dashboard.description.ilike(filter.term + '%%'),
                    Dashboard.label.ilike(filter.term + '%%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_dashboards(
        session, username, groups, data
    ) -> dict:
        return paginate(
            query=DashboardRepository._query_user_dashboards(session, username, groups, data),
            page=data.page,
            page_size=data.pageSize,
        ).to_dict()

    @staticmethod
    def _query_dashboard_shares(session, username, groups, uri, filter) -> Query:
        query = (
            session.query(DashboardShare)
            .join(
                Dashboard,
                Dashboard.dashboardUri == DashboardShare.dashboardUri,
            )
            .filter(
                and_(
                    DashboardShare.dashboardUri == uri,
                    or_(
                        Dashboard.owner == username,
                        Dashboard.SamlGroupName.in_(groups),
                    ),
                )
            )
        )
        if filter and filter.term:
            query = query.filter(
                or_(
                    DashboardShare.SamlGroupName.ilike(
                        filter.term + '%%'
                    ),
                    Dashboard.label.ilike(filter.term + '%%'),
                )
            )
        return query

    @staticmethod
    def query_all_user_groups_shareddashboard(session, groups, uri) -> [str]:
        query = (
            session.query(DashboardShare)
            .filter(
                and_(
                    DashboardShare.dashboardUri == uri,
                    DashboardShare.SamlGroupName.in_(groups),
                )
            )
        )

        return [share.SamlGroupName for share in query.all()]

    @staticmethod
    def paginated_dashboard_shares(
        session, username, groups, uri, data=None
    ) -> dict:
        return paginate(
            query=DashboardRepository._query_dashboard_shares(
                session, username, groups, uri, data
            ),
            page=data.page,
            page_size=data.pageSize,
        ).to_dict()

    @staticmethod
    def delete_dashboard(session, dashboard) -> bool:
        session.delete(dashboard)
        return True

    @staticmethod
    def create_share(
        session,
        username: str,
        dashboard: Dashboard,
        principal_id: str,
        init_status: DashboardShareStatus = DashboardShareStatus.REQUESTED
    ) -> DashboardShare:
        share = DashboardShare(
            owner=username,
            dashboardUri=dashboard.dashboardUri,
            SamlGroupName=principal_id,
            status=init_status.value,
        )
        session.add(share)
        return share

    @staticmethod
    def get_dashboard_share_by_uri(session, uri) -> DashboardShare:
        share: DashboardShare = session.query(DashboardShare).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('DashboardShare', uri)
        return share

    @staticmethod
    def find_share_for_group(session, dashboard_uri, group) -> DashboardShare:
        return (
            session.query(DashboardShare)
            .filter(
                DashboardShare.dashboardUri == dashboard_uri,
                DashboardShare.SamlGroupName == group,
            )
            .first()
        )
