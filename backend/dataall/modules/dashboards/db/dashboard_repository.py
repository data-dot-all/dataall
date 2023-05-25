import logging

from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from dataall.core.group.services.group_resource_manager import EnvironmentResource
from dataall.core.permission_checker import has_tenant_permission, has_resource_permission
from dataall.db import models, exceptions, paginate
from dataall.db.api import (
    Environment,
    ResourcePolicy,
    Glossary,
    Vote,
)
from dataall.modules.dashboards.db.models import DashboardShare, DashboardShareStatus, Dashboard
from dataall.modules.dashboards.services.dashboard_permissions import MANAGE_DASHBOARDS, CREATE_DASHBOARD, \
    DASHBOARD_ALL, GET_DASHBOARD, SHARE_DASHBOARD, UPDATE_DASHBOARD

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
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(CREATE_DASHBOARD)
    def import_dashboard(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
    ) -> Dashboard:
        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data['SamlGroupName'],
            permission_name=CREATE_DASHBOARD,
        )

        env: models.Environment = data.get(
            'environment', Environment.get_environment_by_uri(session, uri)
        )
        dashboard: Dashboard = Dashboard(
            label=data.get('label', 'untitled'),
            environmentUri=data.get('environmentUri'),
            organizationUri=env.organizationUri,
            region=env.region,
            DashboardId=data.get('dashboardId'),
            AwsAccountId=env.AwsAccountId,
            owner=username,
            namespace='test',
            tags=data.get('tags', []),
            SamlGroupName=data['SamlGroupName'],
        )
        session.add(dashboard)
        session.commit()

        activity = models.Activity(
            action='DASHBOARD:CREATE',
            label='DASHBOARD:CREATE',
            owner=username,
            summary=f'{username} created dashboard {dashboard.label} in {env.label}',
            targetUri=dashboard.dashboardUri,
            targetType='dashboard',
        )
        session.add(activity)

        DashboardRepository.set_dashboard_resource_policy(
            session, env, dashboard, data['SamlGroupName']
        )

        if 'terms' in data.keys():
            Glossary.set_glossary_terms_links(
                session,
                username,
                dashboard.dashboardUri,
                'Dashboard',
                data.get('terms', []),
            )
        return dashboard

    @staticmethod
    def set_dashboard_resource_policy(session, environment, dashboard, group):
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=group,
            permissions=DASHBOARD_ALL,
            resource_uri=dashboard.dashboardUri,
            resource_type=Dashboard.__name__,
        )
        if environment.SamlGroupName != dashboard.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=DASHBOARD_ALL,
                resource_uri=dashboard.dashboardUri,
                resource_type=Dashboard.__name__,
            )

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(GET_DASHBOARD)
    def get_dashboard(session, uri: str) -> Dashboard:
        return DashboardRepository.get_dashboard_by_uri(session, uri)

    @staticmethod
    def get_dashboard_by_uri(session, uri) -> Dashboard:
        dashboard: Dashboard = session.query(Dashboard).get(uri)
        if not dashboard:
            raise exceptions.ObjectNotFound('Dashboard', uri)
        return dashboard

    @staticmethod
    def query_user_dashboards(session, username, groups, filter) -> Query:
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
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    Dashboard.description.ilike(filter.get('term') + '%%'),
                    Dashboard.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_dashboards(
        session, username, groups, data=None
    ) -> dict:
        return paginate(
            query=DashboardRepository.query_user_dashboards(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def query_dashboard_shares(session, username, groups, uri, filter) -> Query:
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
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    DashboardShare.SamlGroupName.ilike(
                        filter.get('term') + '%%'
                    ),
                    Dashboard.label.ilike(filter.get('term') + '%%'),
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
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(SHARE_DASHBOARD)
    def paginated_dashboard_shares(
        session, username, groups, uri, data=None
    ) -> dict:
        return paginate(
            query=DashboardRepository.query_dashboard_shares(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(UPDATE_DASHBOARD)
    def update_dashboard(
        session,
        username: str,
        uri: str,
        dashboard: Dashboard,
        data: dict = None,
    ) -> Dashboard:
        for k in data.keys():
            setattr(dashboard, k, data.get(k))

        if 'terms' in data.keys():
            Glossary.set_glossary_terms_links(
                session,
                username,
                dashboard.dashboardUri,
                'Dashboard',
                data.get('terms', []),
            )
        environment: models.Environment = Environment.get_environment_by_uri(
            session, dashboard.environmentUri
        )
        DashboardRepository.set_dashboard_resource_policy(
            session, environment, dashboard, dashboard.SamlGroupName
        )
        return dashboard

    @staticmethod
    def delete_dashboard(session, uri) -> bool:
        # TODO THERE WAS NO PERMISSION CHECK
        dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
        session.delete(dashboard)
        ResourcePolicy.delete_resource_policy(
            session=session, resource_uri=uri, group=dashboard.SamlGroupName
        )
        Glossary.delete_glossary_terms_links(
            session, target_uri=dashboard.dashboardUri, target_type='Dashboard'
        )
        Vote.delete_votes(session, dashboard.dashboardUri, 'dashboard')
        session.commit()
        return True

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    def request_dashboard_share(
        session,
        username: str,
        uri: str,
        principal_id: str
    ) -> DashboardShare:
        dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
        if dashboard.SamlGroupName == principal_id:
            raise exceptions.UnauthorizedOperation(
                action=CREATE_DASHBOARD,
                message=f'Team {dashboard.SamlGroupName} is the owner of the dashboard {dashboard.label}',
            )
        share: DashboardShare = (
            session.query(DashboardShare)
            .filter(
                DashboardShare.dashboardUri == uri,
                DashboardShare.SamlGroupName == principal_id,
            )
            .first()
        )
        if not share:
            share = DashboardShare(
                owner=username,
                dashboardUri=dashboard.dashboardUri,
                SamlGroupName=principal_id,
                status=DashboardShareStatus.REQUESTED.value,
            )
            session.add(share)
        else:
            if share.status not in DashboardShareStatus.__members__:
                raise exceptions.InvalidInput(
                    'Share status',
                    share.status,
                    str(DashboardShareStatus.__members__),
                )
            if share.status == 'REJECTED':
                share.status = 'REQUESTED'

        return share

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(SHARE_DASHBOARD)
    def approve_dashboard_share(session, uri: str, share) -> DashboardShare:
        if share.status == DashboardShareStatus.APPROVED.value:
            return share

        share.status = DashboardShareStatus.APPROVED.value

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=share.SamlGroupName,
            permissions=[GET_DASHBOARD],
            resource_uri=share.dashboardUri,
            resource_type=Dashboard.__name__,
        )

        return share

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(SHARE_DASHBOARD)
    def reject_dashboard_share( session, uri: str, share) -> DashboardShare:
        if share.status == DashboardShareStatus.REJECTED.value:
            return share

        share.status = DashboardShareStatus.REJECTED.value

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=share.SamlGroupName,
            resource_uri=share.dashboardUri,
            resource_type=Dashboard.__name__,
        )

        return share

    @staticmethod
    @has_tenant_permission(MANAGE_DASHBOARDS)
    @has_resource_permission(SHARE_DASHBOARD)
    def share_dashboard(
        session,
        username: str,
        uri: str,
        principal_id: str
    ) -> DashboardShare:

        dashboard = DashboardRepository.get_dashboard_by_uri(session, uri)
        share = DashboardShare(
            owner=username,
            dashboardUri=dashboard.dashboardUri,
            SamlGroupName=principal_id,
            status=DashboardShareStatus.APPROVED.value,
        )
        session.add(share)
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=principal_id,
            permissions=[GET_DASHBOARD],
            resource_uri=dashboard.dashboardUri,
            resource_type=Dashboard.__name__,
        )
        return share

    @staticmethod
    def get_dashboard_share_by_uri(session, uri) -> DashboardShare:
        share: DashboardShare = session.query(DashboardShare).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('DashboardShare', uri)
        return share
