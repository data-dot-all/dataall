import logging
import os

from aws_cdk import Stack
from aws_cdk import cloudformation_include as cfn_inc

from ... import db
from ...db import models
from ...db.api import Environment
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil
from .manager import stack

logger = logging.getLogger(__name__)


@stack(stack="sagemakerstudiouserprofile")
class SagemakerStudioUserProfile(Stack):
    module_name = __file__

    def get_engine(self) -> db.Engine:
        ENVNAME = os.environ.get("envname", "local")
        engine = db.get_engine(envname=ENVNAME)
        return engine

    def get_target(self, target_uri) -> models.SagemakerStudioUserProfile:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            sm_user_profile = session.query(models.SagemakerStudioUserProfile).get(target_uri)
        return sm_user_profile

    def get_env(self, environment_uri) -> models.Environment:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = session.query(models.Environment).get(environment_uri)
        return env

    def get_env_group(self, sm_user_profile: models.SagemakerStudioUserProfile) -> models.EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(
                session,
                sm_user_profile.SamlAdminGroupName,
                sm_user_profile.environmentUri,
            )
        return env

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        sm_user_profile: models.SagemakerStudioUserProfile = self.get_target(target_uri=self.target_uri)

        env_group = self.get_env_group(sm_user_profile)

        cfn_template_user_profile = os.path.join(
            os.path.dirname(__file__), "..", "cfnstacks", "sagemaker-user-template.yaml"
        )
        user_profile_parameters = dict(
            sagemaker_domain_id=sm_user_profile.sagemakerStudioDomainID,
            user_profile_name=sm_user_profile.sagemakerStudioUserProfileNameSlugify,
            execution_role=env_group.environmentIAMRoleArn,
        )
        logger.info(f"Creating the user profile {user_profile_parameters}")

        my_sagemaker_studio_user_template = cfn_inc.CfnInclude(
            self,
            f"SagemakerStudioUserProfile{self.target_uri}",
            template_file=cfn_template_user_profile,
            parameters=user_profile_parameters,
        )

        self.user_profile_arn = (
            my_sagemaker_studio_user_template.get_resource("SagemakerUser").get_att("UserProfileArn").to_string()
        )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)
