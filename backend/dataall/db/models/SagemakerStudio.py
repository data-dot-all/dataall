from sqlalchemy import Column, String
from sqlalchemy.orm import query_expression

from .. import Base
from .. import Resource, utils


class SagemakerStudio(Resource, Base):
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


class SagemakerStudioUserProfile(Resource, Base):
    __tablename__ = 'sagemaker_studio_user_profile'
    environmentUri = Column(String, nullable=False)
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
