"""
DAO layer that encapsulates the logic and interaction with the database for ML Studio
Provides the API to retrieve / update / delete ml studio
"""
from typing import Optional
from sqlalchemy import or_
from sqlalchemy.sql import and_
from sqlalchemy.orm import Query

from dataall.base.utils import slugify
from dataall.base.db import paginate
from dataall.modules.mlstudio.db.mlstudio_models import SagemakerStudioDomain, SagemakerStudioUser
from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)

class SageMakerStudioRepository(EnvironmentResource):
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

    def paginated_sagemaker_studio_users(self, username, groups, filter={}) -> dict:
        """Returns a page of sagemaker studio users for a data.all user"""
        return paginate(
            query=self._query_user_sagemaker_studio_users(username, groups, filter),
            page=filter.get('page', SageMakerStudioRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', SageMakerStudioRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def find_sagemaker_studio_user(self, uri):
        """Finds a sagemaker studio user. Returns None if it doesn't exist"""
        return self._session.query(SagemakerStudioUser).get(uri)

    def count_resources(self, environment, group_uri):
        return (
            self._session.query(SagemakerStudioUser)
            .filter(
                and_(
                    SagemakerStudioUser.environmentUri == environment.environmentUri,
                    SagemakerStudioUser.SamlAdminGroupName == group_uri
                )
            )
            .count()
        )

    def create_sagemaker_studio_domain(self, username, environment, data):
        # TODO: BUILD ROLE ARN Domain Name
        domain = SagemakerStudioDomain(
            label=data.get('label'),
            owner=username,
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            environmentUri=environment.environmentUri,
            AWSAccountId=environment.AwsAccountId,
            region=environment.region,
            SagemakerStudioStatus="PENDING",
            RoleArn="DefaultMLStudioRole",
            sagemakerStudioDomainName=slugify(data.get('label'), separator=''),
            vpcType=data.get('vpcType'),
            vpcId=data.get('vpcId'),
            subnetIds=data.get('subnetIds', [])
        )
        self._session.add(domain)
        self._session.commit()

        domain.sagemakerStudioDomainName = NamingConventionService(
            target_uri=domain.sagemakerStudioUri,
            target_label=domain.label,
            pattern=NamingConventionPattern.MLSTUDIO_DOMAIN,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        domain.RoleArn = NamingConventionService(
            target_uri=domain.sagemakerStudioUri,
            target_label=f"DefaultMLStudioRole-{domain.label}",
            pattern=NamingConventionPattern.IAM,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        return domain

    def paginated_environment_sagemaker_studio_domains(self, uri, filter={}) -> dict:
        """Returns a page of sagemaker studio users for a data.all user"""
        return paginate(
            query=self._query_environment_sagemaker_studio_domains(uri, filter),
            page=filter.get('page', SageMakerStudioRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', SageMakerStudioRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    def _query_environment_sagemaker_studio_domains(self, uri, filter) -> Query:
        query = self._session.query(SagemakerStudioDomain).filter(
            SagemakerStudioDomain.environmentUri == uri,
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    SagemakerStudioDomain.description.ilike(
                        filter.get('term') + '%%'
                    ),
                    SagemakerStudioDomain.label.ilike(
                        filter.get('term') + '%%'
                    ),
                )
            )
        return query

    def find_sagemaker_studio_domain(self, uri) -> Optional[SagemakerStudioDomain]:
        return self._session.query(SagemakerStudioDomain).get(uri)

    @staticmethod
    def get_sagemaker_studio_domain_by_env_uri(session, env_uri) -> Optional[SagemakerStudioDomain]:
        domain: SagemakerStudioDomain = session.query(SagemakerStudioDomain).filter(
            SagemakerStudioDomain.environmentUri == env_uri,
        ).first()
        if not domain:
            return None
        return domain
