""""
Creates a CloudFormation stack for SageMaker Studio users using cdk
"""
import logging
import os

from aws_cdk import (
    cloudformation_include as cfn_inc,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_kms as kms,
    aws_logs as logs,
    aws_sagemaker as sagemaker,
    aws_ssm as ssm,
    RemovalPolicy,
    Stack
)

from botocore.exceptions import ClientError

from dataall.modules.mlstudio.db.models import SagemakerStudioUser
from dataall.db.models import EnvironmentGroup


from dataall.cdkproxy.stacks.manager import stack
from dataall.db import Engine, get_engine
from dataall.db.api import Environment as EnvironmentRepository
from dataall.utils.cdk_nag_utils import CDKNagUtil
from dataall.utils.runtime_stacks_tagging import TagsUtil

from dataall.aws.handlers.sts import SessionHelper
from dataall.aws.handlers.parameter_store import ParameterStoreManager
from dataall.modules.mlstudio.aws.ec2_client import EC2
from dataall.modules.mlstudio.aws.sagemaker_studio_client import get_sagemaker_studio_domain

from dataall.cdkproxy.stacks import EnvironmentSetup
from dataall.cdkproxy.stacks.environment import EnvironmentStackExtension

logger = logging.getLogger(__name__)


class SageMakerDomainExtension(EnvironmentStackExtension):

    @staticmethod
    def extent(setup: EnvironmentSetup):
        _environment = setup.environment()
        sagemaker_principals = [setup.default_role] + setup.group_roles
        logger.info(f'Creating SageMaker base resources for sagemaker_principals = {sagemaker_principals}..')
        cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
            accountid=_environment.AwsAccountId, region=_environment.region
        )
        existing_default_vpc = EC2.check_default_vpc_exists(
            AwsAccountId=_environment.AwsAccountId, region=_environment.region, role=cdk_look_up_role_arn
        )
        if existing_default_vpc:
            logger.info("Using default VPC for Sagemaker Studio domain")
            # Use default VPC - initial configuration (to be migrated)
            vpc = ec2.Vpc.from_lookup(setup, 'VPCStudio', is_default=True)
            subnet_ids = [private_subnet.subnet_id for private_subnet in vpc.private_subnets]
            subnet_ids += [public_subnet.subnet_id for public_subnet in vpc.public_subnets]
            subnet_ids += [isolated_subnet.subnet_id for isolated_subnet in vpc.isolated_subnets]
            security_groups = []
        else:
            logger.info("Default VPC not found, Exception. Creating a VPC for SageMaker resources...")
            # Create VPC with 3 Public Subnets and 3 Private subnets wit NAT Gateways
            log_group = logs.LogGroup(
                setup,
                f'SageMakerStudio{_environment.name}',
                log_group_name=f'/{_environment.resourcePrefix}/{_environment.name}/vpc/sagemakerstudio',
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.DESTROY,
            )
            vpc_flow_role = iam.Role(
                setup, 'FlowLog',
                assumed_by=iam.ServicePrincipal('vpc-flow-logs.amazonaws.com')
            )
            vpc = ec2.Vpc(
                setup,
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
            ec2.FlowLog(
                setup, "StudioVPCFlowLog",
                resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
                destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group, vpc_flow_role)
            )
            # setup security group to be used for sagemaker studio domain
            sagemaker_sg = ec2.SecurityGroup(
                setup,
                "SecurityGroup",
                vpc=vpc,
                description="Security Group for SageMaker Studio",
            )

            sagemaker_sg.add_ingress_rule(sagemaker_sg, ec2.Port.all_traffic())
            security_groups = [sagemaker_sg.security_group_id]
            subnet_ids = [private_subnet.subnet_id for private_subnet in vpc.private_subnets]

        vpc_id = vpc.vpc_id

        sagemaker_domain_role = iam.Role(
            setup,
            'RoleForSagemakerStudioUsers',
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
            role_name='RoleSagemakerStudioUsers',
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    setup,
                    id='SagemakerFullAccess',
                    managed_policy_arn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                ),
                iam.ManagedPolicy.from_managed_policy_arn(
                    setup, id='S3FullAccess', managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
                ),
            ],
        )

        sagemaker_domain_key = kms.Key(
            setup,
            'SagemakerDomainKmsKey',
            alias='SagemakerStudioDomain',
            enable_key_rotation=True,
            policy=iam.PolicyDocument(
                assign_sids=True,
                statements=[
                    iam.PolicyStatement(
                        resources=['*'],
                        effect=iam.Effect.ALLOW,
                        principals=[iam.AccountPrincipal(account_id=_environment.AwsAccountId),
                                    sagemaker_domain_role] + sagemaker_principals,
                        actions=['kms:*'],
                    )
                ],
            ),
        )

        sagemaker_domain = sagemaker.CfnDomain(
            setup,
            'SagemakerStudioDomain',
            domain_name=f'SagemakerStudioDomain-{_environment.region}-{_environment.AwsAccountId}',
            auth_mode='IAM',
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=sagemaker_domain_role.role_arn,
                security_groups=security_groups,
                sharing_settings=sagemaker.CfnDomain.SharingSettingsProperty(
                    notebook_output_option='Allowed',
                    s3_kms_key_id=sagemaker_domain_key.key_id,
                    s3_output_path=f's3://sagemaker-{_environment.region}-{_environment.AwsAccountId}',
                ),
            ),
            vpc_id=vpc_id,
            subnet_ids=subnet_ids,
            app_network_access_type='VpcOnly',
            kms_key_id=sagemaker_domain_key.key_id,
        )

        ssm.StringParameter(
            setup,
            'SagemakerStudioDomainId',
            string_value=sagemaker_domain.attr_domain_id,
            parameter_name=f'/dataall/{_environment.environmentUri}/sagemaker/sagemakerstudio/domain_id',
        )
        return sagemaker_domain

    @staticmethod
    def check_existing_sagemaker_studio_domain(environment):
        logger.info('Check if there is an existing sagemaker studio domain in the account')
        try:
            logger.info('check sagemaker studio domain created as part of data.all environment stack.')
            cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
                accountid=environment.AwsAccountId, region=environment.region
            )
            dataall_created_domain = ParameterStoreManager.client(
                AwsAccountId=environment.AwsAccountId, region=environment.region, role=cdk_look_up_role_arn
            ).get_parameter(Name=f'/dataall/{environment.environmentUri}/sagemaker/sagemakerstudio/domain_id')
            return False
        except ClientError as e:
            logger.info(f'check sagemaker studio domain created outside of data.all. Parameter data.all not found: {e}')
            existing_domain = get_sagemaker_studio_domain(
                AwsAccountId=environment.AwsAccountId, region=environment.region, role=cdk_look_up_role_arn
            )
            return existing_domain.get('DomainId', False)


@stack(stack='sagemakerstudiouserprofile')
class SagemakerStudioUserProfile(Stack):
    """
    Creation of a sagemaker studio user stack.
    Having imported the mlstudio module, the class registers itself using @stack
    Then it will be reachable by HTTP request / using SQS from GraphQL lambda
    """
    module_name = __file__

    def get_engine(self) -> Engine:
        envname = os.environ.get('envname', 'local')
        engine = get_engine(envname=envname)
        return engine

    def get_target(self, target_uri) -> SagemakerStudioUser:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            sm_user = session.query(SagemakerStudioUser).get(
                target_uri
            )
        return sm_user

    def get_env_group(
            self, sm_user: SagemakerStudioUser
    ) -> EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env_group = EnvironmentRepository.get_environment_group(
                session, sm_user.SamlAdminGroupName, sm_user.environmentUri,
            )
        return env_group

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(scope,
                         id,
                         description="Cloud formation stack of SM STUDIO USER: {}; URI: {}; DESCRIPTION: {}".format(
                             self.get_target(target_uri=target_uri).label,
                             target_uri,
                             self.get_target(target_uri=target_uri).description,
                         )[:1024],
                         **kwargs)
        # Required for dynamic stack tagging
        self.target_uri = target_uri
        sm_user: SagemakerStudioUser = self.get_target(target_uri=self.target_uri)
        print(f"sm_user= {sm_user}")
        env_group = self.get_env_group(sm_user)
        cfn_template_user = os.path.join(
            os.path.dirname(__file__), 'cfnstacks', 'sagemaker-user-template.yaml'
        )
        print(f"path:{cfn_template_user}")
        user_parameters = dict(
            sagemaker_domain_id=sm_user.sagemakerStudioDomainID,
            user_profile_name=sm_user.sagemakerStudioUserNameSlugify,
            execution_role=env_group.environmentIAMRoleArn,
        )
        logger.info(f'Creating the SageMaker Studio user {user_parameters}')
        my_sagemaker_studio_user_template = cfn_inc.CfnInclude(
            self,
            f'SagemakerStudioUser{self.target_uri}',
            template_file=cfn_template_user,
            parameters=user_parameters,
        )
        self.sm_user_arn = (
            my_sagemaker_studio_user_template.get_resource('SagemakerUser')
            .get_att('UserProfileArn')
            .to_string()
        )
        TagsUtil.add_tags(stack=self, model=SagemakerStudioUser, target_type="smstudiouser")
        CDKNagUtil.check_rules(self)
