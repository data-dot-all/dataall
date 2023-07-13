import logging

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization import Organization
from dataall.core.vote.db.vote import Vote
from dataall.modules.dashboards import DashboardRepository
from dataall.searchproxy.base_indexer import BaseIndexer
from dataall.modules.dashboards.db.models import Dashboard

log = logging.getLogger(__name__)


class DashboardIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dashboard_uri: str):
        dashboard: Dashboard = DashboardRepository.get_dashboard_by_uri(session, dashboard_uri)

        if dashboard:
            env = EnvironmentService.get_environment_by_uri(session, dashboard.environmentUri)
            org = Organization.get_organization_by_uri(session, env.organizationUri)

            glossary = BaseIndexer._get_target_glossary_terms(session, dashboard_uri)
            count_upvotes = Vote.count_upvotes(
                session, dashboard_uri, target_type='dashboard'
            )
            BaseIndexer._index(
                doc_id=dashboard_uri,
                doc={
                    'name': dashboard.name,
                    'admins': dashboard.SamlGroupName,
                    'owner': dashboard.owner,
                    'label': dashboard.label,
                    'resourceKind': 'dashboard',
                    'description': dashboard.description,
                    'tags': [f.replace('-', '') for f in dashboard.tags or []],
                    'topics': [],
                    'region': dashboard.region.replace('-', ''),
                    'environmentUri': env.environmentUri,
                    'environmentName': env.name,
                    'organizationUri': org.organizationUri,
                    'organizationName': org.name,
                    'created': dashboard.created,
                    'updated': dashboard.updated,
                    'deleted': dashboard.deleted,
                    'glossary': glossary,
                    'upvotes': count_upvotes,
                },
            )
        return dashboard
