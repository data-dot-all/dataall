"""
DAO layer that encapsulates the logic and interaction with the database for Omics
Provides the API to retrieve / update / delete omics resources
"""
from sqlalchemy import or_
from sqlalchemy.sql import and_
from sqlalchemy.orm import Query

from dataall.base.db import paginate, exceptions
from dataall.modules.omics.db.omics_models import OmicsWorkflow, OmicsRun
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource


class OmicsRepository(EnvironmentResource):
    """DAO layer for Omics"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 20

    def __init__(self, session):
        self._session = session

    def save_omics_run(self, omics_run):
        """Save Omics run to the database"""
        self._session.add(omics_run)
        self._session.commit()

    def save_omics_workflow(self, omics_workflow):
        """Save Omics run to the database"""
        self._session.add(omics_workflow)
        self._session.commit()

    def delete_omics_run(self, omics_run):
        """Delete Omics run from the database"""
        self._session.delete(omics_run)
        self._session.commit()

    def delete_omics_workflow(self, omics_workflow):
        """Delete Omics workflow from the database"""
        self._session.delete(omics_workflow)
        self._session.commit()

    def get_workflow(self, workflowUri: str):
        return self._session.query(OmicsWorkflow).get(workflowUri)

    def get_omics_run(self, runUri: str):
        omics_run = self._session.query(OmicsRun).get(runUri)
        if not omics_run:
            raise exceptions.ObjectNotFound("OmicsRun", runUri)
        return omics_run

    def _query_workflows(self, filter) -> Query:
        query = self._session.query(OmicsWorkflow)
        if filter and filter.get("term"):
            query = query.filter(
                or_(
                    OmicsWorkflow.id.ilike(filter.get("term") + "%%"),
                    OmicsWorkflow.name.ilike("%%" + filter.get("term") + "%%"),
                )
            )
        return query

    def paginated_omics_workflows(self, filter=None) -> dict:
        return paginate(
            query=self._query_workflows(filter),
            page=filter.get('page', OmicsRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', OmicsRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def _query_user_runs(self, username, groups, filter) -> Query:
        query = self._session.query(OmicsRun).filter(
            or_(
                OmicsRun.owner == username,
                OmicsRun.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get("term"):
            query = query.filter(
                or_(
                    OmicsRun.description.ilike(filter.get("term") + "%%"),
                    OmicsRun.label.ilike(filter.get("term") + "%%"),
                )
            )
        return query

    def paginated_user_runs(self, username, groups, filter=None) -> dict:
        return paginate(
            query=self._query_user_runs(username, groups, filter),
            page=filter.get('page', OmicsRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', OmicsRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def count_resources(self, environment, group_uri):
        return (
            self._session.query(OmicsRun)
            .filter(
                and_(
                    OmicsRun.environmentUri == environment.environmentUri,
                    OmicsRun.SamlAdminGroupName == group_uri
                )
            )
            .count()
        )
