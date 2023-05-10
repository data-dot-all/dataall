"""
DAO layer that encapsulates the logic and interaction with the database for ML Studio
Provides the API to retrieve / update / delete ml studio
"""
from sqlalchemy import or_
from sqlalchemy.orm import Query

from dataall.db import paginate, exceptions
from dataall.modules.mlstudio.db.models import SagemakerStudioUser


class SageMakerStudioRepository:
    """DAO layer for ML Studio"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    def __init__(self, session):
        self._session = session

    def save_sagemaker_studio_user(self, user):
        """Save SageMaker Studio user to the database"""
        self._session.add(user)
        self._session.commit()

    def _query_user_sagemaker_studio_users(self, username, groups, filter) -> Query:
        query = self._session.query(SagemakerStudioUser).filter(
            or_(
                SagemakerStudioUser.owner == username,
                SagemakerStudioUser.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    SagemakerStudioUser.description.ilike(
                        filter.get('term') + '%%'
                    ),
                    SagemakerStudioUser.label.ilike(
                        filter.get('term') + '%%'
                    ),
                )
            )
        return query

    def paginated_sagemaker_studio_users(self, username, groups, filter=None) -> dict:
        """Returns a page of sagemaker studio users for a data.all user"""
        return paginate(
            query=self._query_user_sagemaker_studio_users(username, groups, filter),
            page=filter.get('page', SageMakerStudioRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', SageMakerStudioRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def find_sagemaker_studio_user(self, uri):
        """Finds a sagemaker studio user. Returns None if it doesn't exist"""
        return self._session.query(SagemakerStudioUser).get(uri)

    def count_sagemaker_studio_user(self, environment_uri):
        return (
            self._session.query(SagemakerStudioUser)
            .filter(SagemakerStudioUser.environmentUri == environment_uri)
            .count()
        )
