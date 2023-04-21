import logging

from .. import db
from ..db import models
from dataall.searchproxy.upsert import BaseIndexer

log = logging.getLogger(__name__)


class DashboardIndexer(BaseIndexer):
    @classmethod
    def upsert(cls, session, dashboard_uri: str):
        dashboard = (
            session.query(
                models.Dashboard.dashboardUri.label('uri'),
                models.Dashboard.name.label('name'),
                models.Dashboard.owner.label('owner'),
                models.Dashboard.label.label('label'),
                models.Dashboard.description.label('description'),
                models.Dashboard.tags.label('tags'),
                models.Dashboard.region.label('region'),
                models.Organization.organizationUri.label('orgUri'),
                models.Organization.name.label('orgName'),
                models.Environment.environmentUri.label('envUri'),
                models.Environment.name.label('envName'),
                models.Dashboard.SamlGroupName.label('admins'),
                models.Dashboard.created,
                models.Dashboard.updated,
                models.Dashboard.deleted,
            )
            .join(
                models.Organization,
                models.Dashboard.organizationUri == models.Dashboard.organizationUri,
            )
            .join(
                models.Environment,
                models.Dashboard.environmentUri == models.Environment.environmentUri,
            )
            .filter(models.Dashboard.dashboardUri == dashboard_uri)
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
