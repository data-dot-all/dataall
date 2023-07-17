import logging

from sqlalchemy import or_, and_
from sqlalchemy.orm import Query

from .. import models, exceptions, permissions, paginate
from . import (
    Environment,
    has_tenant_perm,
    has_resource_perm,
    ResourcePolicy,
    Glossary,
    Vote,
)

logger = logging.getLogger(__name__)


class Dashboard:
    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.CREATE_DASHBOARD)
    def import_dashboard(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.Dashboard:
        if not data:
            raise exceptions.RequiredParameter(data)
        if not data.get('environmentUri'):
            raise exceptions.RequiredParameter('environmentUri')
        if not data.get('SamlGroupName'):
            raise exceptions.RequiredParameter('group')
        if not data.get('dashboardId'):
            raise exceptions.RequiredParameter('dashboardId')
        if not data.get('label'):
            raise exceptions.RequiredParameter('label')

        Environment.check_group_environment_permission(
            session=session,
            username=username,
            groups=groups,
            uri=uri,
            group=data['SamlGroupName'],
            permission_name=permissions.CREATE_DASHBOARD,
        )

        env: models.Environment = data.get(
            'environment', Environment.get_environment_by_uri(session, uri)
        )
        dashboard: models.Dashboard = models.Dashboard(
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

        Dashboard.set_dashboard_resource_policy(
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
            permissions=permissions.DASHBOARD_ALL,
            resource_uri=dashboard.dashboardUri,
            resource_type=models.Dashboard.__name__,
        )
        if environment.SamlGroupName != dashboard.SamlGroupName:
            ResourcePolicy.attach_resource_policy(
                session=session,
                group=environment.SamlGroupName,
                permissions=permissions.DASHBOARD_ALL,
                resource_uri=dashboard.dashboardUri,
                resource_type=models.Dashboard.__name__,
            )

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.GET_DASHBOARD)
    def get_dashboard(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.Dashboard:
        return Dashboard.get_dashboard_by_uri(session, uri)

    @staticmethod
    def get_dashboard_by_uri(session, uri) -> models.Dashboard:
        dashboard: models.Dashboard = session.query(models.Dashboard).get(uri)
        if not dashboard:
            raise exceptions.ObjectNotFound('Dashboard', uri)
        return dashboard

    @staticmethod
    def query_user_dashboards(session, username, groups, filter) -> Query:
        query = (
            session.query(models.Dashboard)
            .outerjoin(
                models.DashboardShare,
                models.Dashboard.dashboardUri == models.DashboardShare.dashboardUri,
            )
            .filter(
                or_(
                    models.Dashboard.owner == username,
                    models.Dashboard.SamlGroupName.in_(groups),
                    and_(
                        models.DashboardShare.SamlGroupName.in_(groups),
                        models.DashboardShare.status
                        == models.DashboardShareStatus.APPROVED.value,
                    ),
                )
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    models.Dashboard.description.ilike(filter.get('term') + '%%'),
                    models.Dashboard.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    @staticmethod
    def paginated_user_dashboards(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Dashboard.query_user_dashboards(session, username, groups, data),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    def query_dashboard_shares(session, username, groups, uri, filter) -> Query:
        query = (
            session.query(models.DashboardShare)
            .join(
                models.Dashboard,
                models.Dashboard.dashboardUri == models.DashboardShare.dashboardUri,
            )
            .filter(
                and_(
                    models.DashboardShare.dashboardUri == uri,
                    or_(
                        models.Dashboard.owner == username,
                        models.Dashboard.SamlGroupName.in_(groups),
                    ),
                )
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    models.DashboardShare.SamlGroupName.ilike(
                        filter.get('term') + '%%'
                    ),
                    models.Dashboard.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query

    @staticmethod
    def query_all_user_groups_shareddashboard(session, username, groups, uri) -> Query:
        query = (
            session.query(models.DashboardShare)
            .filter(
                and_(
                    models.DashboardShare.dashboardUri == uri,
                    models.DashboardShare.SamlGroupName.in_(groups),
                )
            )
        )

        return [
            share.SamlGroupName
            for share in query.all()
        ]

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.SHARE_DASHBOARD)
    def paginated_dashboard_shares(
        session, username, groups, uri, data=None, check_perm=None
    ) -> dict:
        return paginate(
            query=Dashboard.query_dashboard_shares(
                session, username, groups, uri, data
            ),
            page=data.get('page', 1),
            page_size=data.get('pageSize', 10),
        ).to_dict()

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.UPDATE_DASHBOARD)
    def update_dashboard(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.Dashboard:

        dashboard = data.get(
            'dashboard',
            Dashboard.get_dashboard_by_uri(session, data['dashboardUri']),
        )

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
        Dashboard.set_dashboard_resource_policy(
            session, environment, dashboard, dashboard.SamlGroupName
        )
        return dashboard

    @staticmethod
    def delete_dashboard(
        session, username, groups, uri, data=None, check_perm=None
    ) -> bool:
        dashboard = Dashboard.get_dashboard_by_uri(session, uri)
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
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    def request_dashboard_share(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DashboardShare:
        dashboard = Dashboard.get_dashboard_by_uri(session, uri)
        if dashboard.SamlGroupName == data['principalId']:
            raise exceptions.UnauthorizedOperation(
                action=permissions.CREATE_DASHBOARD,
                message=f'Team {dashboard.SamlGroupName} is the owner of the dashboard {dashboard.label}',
            )
        share: models.DashboardShare = (
            session.query(models.DashboardShare)
            .filter(
                models.DashboardShare.dashboardUri == uri,
                models.DashboardShare.SamlGroupName == data['principalId'],
            )
            .first()
        )
        if not share:
            share = models.DashboardShare(
                owner=username,
                dashboardUri=dashboard.dashboardUri,
                SamlGroupName=data['principalId'],
                status=models.DashboardShareStatus.REQUESTED.value,
            )
            session.add(share)
        else:
            if share.status not in models.DashboardShareStatus.__members__:
                raise exceptions.InvalidInput(
                    'Share status',
                    share.status,
                    str(models.DashboardShareStatus.__members__),
                )
            if share.status == 'REJECTED':
                share.status = 'REQUESTED'

        return share

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.SHARE_DASHBOARD)
    def approve_dashboard_share(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DashboardShare:

        share: models.DashboardShare = data.get(
            'share', session.query(models.DashboardShare).get(data['shareUri'])
        )

        if share.status not in models.DashboardShareStatus.__members__:
            raise exceptions.InvalidInput(
                'Share status',
                share.status,
                str(models.DashboardShareStatus.__members__),
            )
        if share.status == models.DashboardShareStatus.APPROVED.value:
            return share

        share.status = models.DashboardShareStatus.APPROVED.value

        ResourcePolicy.attach_resource_policy(
            session=session,
            group=share.SamlGroupName,
            permissions=[permissions.GET_DASHBOARD],
            resource_uri=share.dashboardUri,
            resource_type=models.Dashboard.__name__,
        )

        return share

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.SHARE_DASHBOARD)
    def reject_dashboard_share(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DashboardShare:

        share: models.DashboardShare = data.get(
            'share', session.query(models.DashboardShare).get(data['shareUri'])
        )

        if share.status not in models.DashboardShareStatus.__members__:
            raise exceptions.InvalidInput(
                'Share status',
                share.status,
                str(models.DashboardShareStatus.__members__),
            )
        if share.status == models.DashboardShareStatus.REJECTED.value:
            return share

        share.status = models.DashboardShareStatus.REJECTED.value

        ResourcePolicy.delete_resource_policy(
            session=session,
            group=share.SamlGroupName,
            resource_uri=share.dashboardUri,
            resource_type=models.Dashboard.__name__,
        )

        return share

    @staticmethod
    @has_tenant_perm(permissions.MANAGE_DASHBOARDS)
    @has_resource_perm(permissions.SHARE_DASHBOARD)
    def share_dashboard(
        session,
        username: str,
        groups: [str],
        uri: str,
        data: dict = None,
        check_perm: bool = False,
    ) -> models.DashboardShare:

        dashboard = Dashboard.get_dashboard_by_uri(session, uri)
        share = models.DashboardShare(
            owner=username,
            dashboardUri=dashboard.dashboardUri,
            SamlGroupName=data['principalId'],
            status=models.DashboardShareStatus.APPROVED.value,
        )
        session.add(share)
        ResourcePolicy.attach_resource_policy(
            session=session,
            group=data['principalId'],
            permissions=[permissions.GET_DASHBOARD],
            resource_uri=dashboard.dashboardUri,
            resource_type=models.Dashboard.__name__,
        )
        return share

    @staticmethod
    def get_dashboard_share_by_uri(session, uri) -> models.DashboardShare:
        share: models.DashboardShare = session.query(models.DashboardShare).get(uri)
        if not share:
            raise exceptions.ObjectNotFound('DashboardShare', uri)
        return share
