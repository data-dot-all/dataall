import logging

from dataall import db
from dataall.db import models
from dataall.searchproxy.base_indexer import BaseIndexer
from dataall.modules.dashboards.db.models import Dashboard

log = logging.getLogger(__name__)


class DashboardIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dashboard_uri: str):
        dashboard = (
            session.query(
                Dashboard.dashboardUri.label('uri'),
                Dashboard.name.label('name'),
                Dashboard.owner.label('owner'),
                Dashboard.label.label('label'),
                Dashboard.description.label('description'),
                Dashboard.tags.label('tags'),
                Dashboard.region.label('region'),
                models.Organization.organizationUri.label('orgUri'),
                models.Organization.name.label('orgName'),
                models.Environment.environmentUri.label('envUri'),
                models.Environment.name.label('envName'),
                Dashboard.SamlGroupName.label('admins'),
                Dashboard.created,
                Dashboard.updated,
                Dashboard.deleted,
            )
            .join(
                models.Organization,
                Dashboard.organizationUri == Dashboard.organizationUri,
            )
            .join(
                models.Environment,
                Dashboard.environmentUri == models.Environment.environmentUri,
            )
            .filter(Dashboard.dashboardUri == dashboard_uri)
            .first()
        )
        if dashboard:
            glossary = BaseIndexer._get_target_glossary_terms(session, dashboard_uri)
            count_upvotes = db.api.Vote.count_upvotes(
                session, None, None, dashboard_uri, {'targetType': 'dashboard'}
            )
            BaseIndexer._index(
                doc_id=dashboard_uri,
                doc={
                    'name': dashboard.name,
                    'admins': dashboard.admins,
                    'owner': dashboard.owner,
                    'label': dashboard.label,
                    'resourceKind': 'dashboard',
                    'description': dashboard.description,
                    'tags': [f.replace('-', '') for f in dashboard.tags or []],
                    'topics': [],
                    'region': dashboard.region.replace('-', ''),
                    'environmentUri': dashboard.envUri,
                    'environmentName': dashboard.envName,
                    'organizationUri': dashboard.orgUri,
                    'organizationName': dashboard.orgName,
                    'created': dashboard.created,
                    'updated': dashboard.updated,
                    'deleted': dashboard.deleted,
                    'glossary': glossary,
                    'upvotes': count_upvotes,
                },
            )
        return dashboard
