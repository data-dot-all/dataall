"""ORM models for sagemaker studio"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import query_expression

from dataall.db import Base
from dataall.db import Resource, utils


class SagemakerStudioDomain(Resource, Base):
    """Describes ORM model for sagemaker ML Studio domain"""
    __tablename__ = 'sagemaker_studio_domain'
    environmentUri = Column(String, nullable=False)
    sagemakerStudioUri = Column(
        String, primary_key=True, default=utils.uuid('sagemakerstudio')
    )
    sagemakerStudioDomainID = Column(String, nullable=False)
    SagemakerStudioStatus = Column(String, nullable=False)
    AWSAccountId = Column(String, nullable=False)
    RoleArn = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    userRoleForSagemakerStudio = query_expression()


class SagemakerStudioUser(Resource, Base):
    """Describes ORM model for sagemaker ML Studio user"""
    __tablename__ = 'sagemaker_studio_user_profile'
    environmentUri = Column(String, ForeignKey("environment.environmentUri"), nullable=False)
    sagemakerStudioUserProfileUri = Column(
        String, primary_key=True, default=utils.uuid('sagemakerstudiouserprofile')
    )
    sagemakerStudioUserProfileStatus = Column(String, nullable=False)
    sagemakerStudioUserProfileName = Column(String, nullable=False)
    sagemakerStudioUserProfileNameSlugify = Column(
        String, nullable=False, default=utils.slugifier('label')
    )
    sagemakerStudioDomainID = Column(String, nullable=False)
    AWSAccountId = Column(String, nullable=False)
    RoleArn = Column(String, nullable=False)
    region = Column(String, default='eu-west-1')
    SamlAdminGroupName = Column(String, nullable=True)
    userRoleForSagemakerStudioUserProfile = query_expression()


