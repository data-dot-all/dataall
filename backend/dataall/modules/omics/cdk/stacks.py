""""
Creates a CloudFormation stack for Omics projects using cdk
"""
import logging
import os

from aws_cdk import (
    aws_sagemaker as sagemaker,
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_iam as iam,
    Stack,
    CfnOutput,
)

from dataall.modules.omics.db.models import OmicsProject
from dataall.modules.omics.db import models
from dataall.db.models import EnvironmentGroup

from dataall.cdkproxy.stacks.manager import stack
from dataall.db import Engine, get_engine
from dataall.db.api import Environment
from dataall.utils.cdk_nag_utils import CDKNagUtil
from dataall.utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack(stack='omics_project')
class OmicsProjectStack(Stack):
    """
    Creation of an Omics project stack.
    Having imported the omics module, the class registers itself using @stack
    Then it will be reachable by HTTP request / using SQS from GraphQL lambda
    """

    module_name = __file__

    def get_engine(self) -> Engine:
        envname = os.environ.get('envname', 'local')
        engine = get_engine(envname=envname)
        return engine

    def get_target(self, target_uri) -> OmicsProject:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            project = session.query(OmicsProject).get(target_uri)
        return project

    def get_env_group(
        self, project: OmicsProject
    ) -> EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(
                session, project.SamlAdminGroupName, project.environmentUri
            )
        return env

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(scope,
                         id,
                         description="Cloud formation stack of OMICS PROJECT: {}; URI: {}; DESCRIPTION: {}".format(
                             self.get_target(target_uri=target_uri).label,
                             target_uri,
                             self.get_target(target_uri=target_uri).description,
                         )[:1024],
                         **kwargs)

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        omics_project = self.get_target(target_uri=target_uri)

        env_group = self.get_env_group(omics_project)

        #TODO: Define stack if needed

        TagsUtil.add_tags(stack=self, model=models.OmicsProject, target_type="omics_project")

        CDKNagUtil.check_rules(self)
