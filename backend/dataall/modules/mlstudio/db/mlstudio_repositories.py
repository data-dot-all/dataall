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
from dataall.base.utils.naming_convention import (
    NamingConventionService,
    NamingConventionPattern,
)


class SageMakerStudioRepository:
    """DAO layer for ML Studio"""

    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10

    @staticmethod
    def save_sagemaker_studio_user(session, user):
        """Save SageMaker Studio user to the database"""
        session.add(user)
        session.commit()

    @staticmethod
    def _query_user_sagemaker_studio_users(session, username, groups, filter) -> Query:
        query = session.query(SagemakerStudioUser).filter(
            or_(
                SagemakerStudioUser.owner == username,
                SagemakerStudioUser.SamlAdminGroupName.in_(groups),
            )
        )
        if filter and filter.get('term'):
            query = query.filter(
                or_(
                    SagemakerStudioUser.description.ilike(filter.get('term') + '%%'),
                    SagemakerStudioUser.label.ilike(filter.get('term') + '%%'),
                )
            )
        return query.order_by(SagemakerStudioUser.label)

    @staticmethod
    def paginated_sagemaker_studio_users(session, username, groups, filter={}) -> dict:
        """Returns a page of sagemaker studio users for a data.all user"""
        return paginate(
            query=SageMakerStudioRepository._query_user_sagemaker_studio_users(session, username, groups, filter),
            page=filter.get('page', SageMakerStudioRepository._DEFAULT_PAGE),
            page_size=filter.get('pageSize', SageMakerStudioRepository._DEFAULT_PAGE_SIZE),
        ).to_dict()

    @staticmethod
    def find_sagemaker_studio_user(session, uri):
        """Finds a sagemaker studio user. Returns None if it doesn't exist"""
        return session.query(SagemakerStudioUser).get(uri)

    @staticmethod
    def count_resources(session, environment, group_uri):
        return (
            session.query(SagemakerStudioUser)
            .filter(
                and_(
                    SagemakerStudioUser.environmentUri == environment.environmentUri,
                    SagemakerStudioUser.SamlAdminGroupName == group_uri,
                )
            )
            .count()
        )

    @staticmethod
    def create_sagemaker_studio_domain(session, username, environment, data):
        domain = SagemakerStudioDomain(
            label=f'{data.get("label")}-domain',
            owner=username,
            description=data.get('description', 'No description provided'),
            tags=data.get('tags', []),
            SamlGroupName=environment.SamlGroupName,
            environmentUri=environment.environmentUri,
            AWSAccountId=environment.AwsAccountId,
            region=environment.region,
            SagemakerStudioStatus='PENDING',
            DefaultDomainRoleName='DefaultMLStudioRole',
            sagemakerStudioDomainName=slugify(data.get('label'), separator=''),
            vpcType=data.get('vpcType'),
            vpcId=data.get('vpcId'),
            subnetIds=data.get('subnetIds', []),
        )
        session.add(domain)
        session.commit()

        domain.sagemakerStudioDomainName = NamingConventionService(
            target_uri=domain.sagemakerStudioUri,
            target_label=domain.label,
            pattern=NamingConventionPattern.MLSTUDIO_DOMAIN,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        domain.DefaultDomainRoleName = NamingConventionService(
            target_uri=domain.sagemakerStudioUri,
            target_label=domain.label,
            pattern=NamingConventionPattern.IAM,
            resource_prefix=environment.resourcePrefix,
        ).build_compliant_name()

        return domain

    @staticmethod
    def get_sagemaker_studio_domain_by_env_uri(session, env_uri) -> Optional[SagemakerStudioDomain]:
        domain: SagemakerStudioDomain = (
            session.query(SagemakerStudioDomain)
            .filter(
                SagemakerStudioDomain.environmentUri == env_uri,
            )
            .first()
        )
        if not domain:
            return None
        return domain

    @staticmethod
    def delete_sagemaker_studio_domain_by_env_uri(session, env_uri) -> Optional[SagemakerStudioDomain]:
        domain: SagemakerStudioDomain = (
            session.query(SagemakerStudioDomain)
            .filter(
                SagemakerStudioDomain.environmentUri == env_uri,
            )
            .first()
        )
        if domain:
            session.delete(domain)
