"""
DAO layer that encapsulates the logic and interaction with the database for Omics
Provides the API to retrieve / update / delete omics resources
"""

from sqlalchemy import or_
from sqlalchemy.sql import and_
from sqlalchemy.orm import Query

from dataall.base.db import paginate, exceptions
from dataall.core.environment.db.environment_models import Environment, EnvironmentParameter
from dataall.modules.omics.db.omics_models import OmicsWorkflow, OmicsRun


class OmicsRepository:
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

    def get_workflow(self, workflowUri: str):
        return self._session.query(OmicsWorkflow).get(workflowUri)

    def get_workflow_by_id(self, id: str):
        return self._session.query(OmicsWorkflow).filter(OmicsWorkflow.id == id).first()

    def get_omics_run(self, runUri: str):
        omics_run = self._session.query(OmicsRun).get(runUri)
        if not omics_run:
            raise exceptions.ObjectNotFound('OmicsRun', runUri)
        return omics_run

    def _query_workflows(self, filter) -> Query:
        query = self._session.query(OmicsWorkflow)
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    OmicsWorkflow.id.ilike(filter.get('term') + '%%'),
                    OmicsWorkflow.name.ilike('%%' + filter.get('term') + '%%'),
                )
            )
        return query.order_by(OmicsWorkflow.label)

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
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    OmicsRun.description.ilike(filter.get('term') + '%%'),
                    OmicsRun.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(OmicsRun.label)

    def paginated_user_runs(self, username, groups, filter=None) -> dict:
        return paginate(
            query=self._query_user_runs(username, groups, filter),
            page=filter.get('page', OmicsRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', OmicsRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def list_environments_with_omics_enabled(self):
        query = (
            self._session.query(Environment)
            .join(
                EnvironmentParameter,
                EnvironmentParameter.environmentUri == Environment.environmentUri,
            )
            .filter(and_(EnvironmentParameter.key == 'omicsEnabled', EnvironmentParameter.value == 'true'))
        )
        return query.order_by(Environment.label).all()
