import logging
import os
import pathlib
from constructs import Construct
from aws_cdk import (
    cloudformation_include as cfn_inc,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_kms as kms,
    aws_lambda as _lambda,
    aws_sagemaker as sagemaker,
    aws_ssm as ssm,
    CustomResource,
    Duration,
    NestedStack,
    Stack
)
from botocore.exceptions import ClientError
from .manager import stack
from ... import db
from ...db import models
from ...db.api import Environment
from ...aws.handlers.parameter_store import ParameterStoreManager
from ...aws.handlers.sts import SessionHelper
from ...aws.handlers.sagemaker_studio import (
    SagemakerStudio,
)
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


class SageMakerDomain:
    def __init__(
        self,
        stack,
        id,
        environment: models.Environment
    ):
        self.stack = stack
        self.id = id
        self.environment = environment

    def check_existing_sagemaker_studio_domain(self):
        logger.info('Check if there is an existing sagemaker studio domain in the account')
        try:
            logger.info('check sagemaker studio domain created as part of data.all environment stack.')
            cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
                accountid=self.environment.AwsAccountId, region=self.environment.region
            )
            dataall_created_domain = ParameterStoreManager.client(
                AwsAccountId=self.environment.AwsAccountId, region=self.environment.region, role=cdk_look_up_role_arn
            ).get_parameter(Name=f'/dataall/{self.environment.environmentUri}/sagemaker/sagemakerstudio/domain_id')
            return False
        except ClientError as e:
            logger.info(f'check sagemaker studio domain created outside of data.all. Parameter data.all not found: {e}')
            existing_domain = SagemakerStudio.get_sagemaker_studio_domain(
                AwsAccountId=self.environment.AwsAccountId, region=self.environment.region, role=cdk_look_up_role_arn
            )
            return existing_domain.get('DomainId', False)

    def create_sagemaker_domain_resources(self, dependency_group):

        # Create VPC with 3 Public Subnets and 3 Private subnets wit NAT Gateways
        vpc = ec2.Vpc(
            self,
            "SageMakerVPC",
            max_azs=3,
            cidr="10.10.0.0/16",
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT,
                    name="Private",
                    cidr_mask=24
                ),
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        vpc_id = vpc.vpc_id
        subnet_ids = [private_subnet.subnet_id for private_subnet in vpc.private_subnets]
        security_groups = vpc.vpc_default_security_group

        sagemaker_domain_role = iam.Role(
            self,
            'RoleForSagemakerStudioUsers',
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
            role_name='RoleSagemakerStudioUsers',
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    id='SagemakerFullAccess',
                    managed_policy_arn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                ),
                iam.ManagedPolicy.from_managed_policy_arn(
                    self, id='S3FullAccess', managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
                ),
            ],
        )

        sagemaker_domain_key = kms.Key(
            self,
            'SagemakerDomainKmsKey',
            alias='SagemakerStudioDomain',
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                assign_sids=True,
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[iam.AccountPrincipal(account_id=self.environment.AwsAccountId), sagemaker_domain_role] + sagemaker_principals,
                        actions=['kms:*'],
                    )
                ],
            ),
        )
        sagemaker_domain_key.node.add_dependency(dependency_group)

        sagemaker_domain = sagemaker.CfnDomain(
            self,
            'SagemakerStudioDomain',
            domain_name=f'SagemakerStudioDomain-{self.environment.region}-{self.environment.AwsAccountId}',
            auth_mode='IAM',
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=sagemaker_domain_role.role_arn,
                security_groups=security_groups,
                sharing_settings=sagemaker.CfnDomain.SharingSettingsProperty(
                    notebook_output_option='Allowed',
                    s3_kms_key_id=sagemaker_domain_key.key_id,
                    s3_output_path=f's3://sagemaker-{self.environment.region}-{self.environment.AwsAccountId}',
                ),
            ),
            vpc_id=vpc_id,
            subnet_ids=subnet_ids,
            app_network_access_type='VpcOnly',
            kms_key_id=sagemaker_domain_key.key_id,
        )

        ssm.StringParameter(
            self,
            'SagemakerStudioDomainId',
            string_value=sagemaker_domain.attr_domain_id,
            parameter_name=f'/dataall/{self.environment.environmentUri}/sagemaker/sagemakerstudio/domain_id',
        )


@stack(stack='sagemakerstudiouserprofile')
class SagemakerStudioUserProfile(Stack):
    module_name = __file__

    def get_engine(self) -> db.Engine:
        ENVNAME = os.environ.get('envname', 'local')
        engine = db.get_engine(envname=ENVNAME)
        return engine

    def get_target(self, target_uri) -> models.SagemakerStudioUserProfile:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            sm_user_profile = session.query(models.SagemakerStudioUserProfile).get(
                target_uri
            )
        return sm_user_profile

    def get_env(self, environment_uri) -> models.Environment:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = session.query(models.Environment).get(environment_uri)
        return env

    def get_env_group(
        self, sm_user_profile: models.SagemakerStudioUserProfile
    ) -> models.EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(
                session,
                sm_user_profile.SamlAdminGroupName,
                sm_user_profile.environmentUri,
            )
        return env

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(scope,
                         id,
                         description="Cloud formation stack of SM STUDIO PROFILE: {}; URI: {}; DESCRIPTION: {}".format(
                             self.get_target(target_uri=target_uri).label,
                             target_uri,
                             self.get_target(target_uri=target_uri).description,
                         )[:1024],
                         **kwargs)

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        sm_user_profile: models.SagemakerStudioUserProfile = self.get_target(
            target_uri=self.target_uri
        )

        env_group = self.get_env_group(sm_user_profile)

        # SageMaker Studio User Profile
        cfn_template_user_profile = os.path.join(
            os.path.dirname(__file__), '..', 'cfnstacks', 'sagemaker-user-template.yaml'
        )
        user_profile_parameters = dict(
            sagemaker_domain_id=sm_user_profile.sagemakerStudioDomainID,
            user_profile_name=sm_user_profile.sagemakerStudioUserProfileNameSlugify,
            execution_role=env_group.environmentIAMRoleArn,
        )
        logger.info(f'Creating the user profile {user_profile_parameters}')

        my_sagemaker_studio_user_template = cfn_inc.CfnInclude(
            self,
            f'SagemakerStudioUserProfile{self.target_uri}',
            template_file=cfn_template_user_profile,
            parameters=user_profile_parameters,
        )

        self.user_profile_arn = (
            my_sagemaker_studio_user_template.get_resource('SagemakerUser')
            .get_att('UserProfileArn')
            .to_string()
        )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)
