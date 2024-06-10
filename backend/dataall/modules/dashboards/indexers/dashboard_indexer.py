import logging

from dataall.core.environment.services.environment_service import EnvironmentService
from dataall.core.organizations.db.organization_repositories import OrganizationRepository
from dataall.modules.vote.db.vote_repositories import VoteRepository
from dataall.modules.dashboards.db.dashboard_repositories import DashboardRepository
from dataall.modules.dashboards.db.dashboard_models import Dashboard
from dataall.modules.catalog.indexers.base_indexer import BaseIndexer

log = logging.getLogger(__name__)


class DashboardIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dashboard_uri: str):
        dashboard: Dashboard = DashboardRepository.get_dashboard_by_uri(session, dashboard_uri)

        if dashboard:
            env = EnvironmentService.get_environment_by_uri(session, dashboard.environmentUri)
            org = OrganizationRepository.get_organization_by_uri(session, env.organizationUri)

            glossary = BaseIndexer._get_target_glossary_terms(session, dashboard_uri)
            count_upvotes = VoteRepository.count_upvotes(session, dashboard_uri, target_type='dashboard')
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
