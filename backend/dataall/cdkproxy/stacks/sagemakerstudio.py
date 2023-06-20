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
from .manager import stack
from ... import db
from ...db import models
from ...db.api import Environment
from ...aws.handlers.parameter_store import ParameterStoreManager
from ...aws.handlers.sts import SessionHelper
from ...aws.handlers.sagemaker_studio import SagemakerStudio
from ...aws.handlers.ec2 import EC2
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


class SageMakerDomain:
    def __init__(
        self,
        stack,
        id,
        environment: models.Environment,
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

    def create_sagemaker_domain_resources(self, sagemaker_principals):
        logger.info('Creating SageMaker base resources..')
        cdk_look_up_role_arn = SessionHelper.get_cdk_look_up_role_arn(
            accountid=self.environment.AwsAccountId, region=self.environment.region
        )
        existing_default_vpc = EC2.check_default_vpc_exists(
            AwsAccountId=self.environment.AwsAccountId, region=self.environment.region, role=cdk_look_up_role_arn
        )
        if existing_default_vpc:
            logger.info("Using default VPC for Sagemaker Studio domain")
            # Use default VPC - initial configuration (to be migrated)
            vpc = ec2.Vpc.from_lookup(self.stack, 'VPCStudio', is_default=True)
            subnet_ids = [private_subnet.subnet_id for private_subnet in vpc.private_subnets]
            subnet_ids += [public_subnet.subnet_id for public_subnet in vpc.public_subnets]
            subnet_ids += [isolated_subnet.subnet_id for isolated_subnet in vpc.isolated_subnets]
            security_groups = []
        else:
            logger.info("Default VPC not found, Exception. Creating a VPC for SageMaker resources...")
            # Create VPC with 3 Public Subnets and 3 Private subnets wit NAT Gateways
            log_group = logs.LogGroup(
                self.stack,
                f'SageMakerStudio{self.environment.name}',
                log_group_name=f'/{self.environment.resourcePrefix}/{self.environment.name}/vpc/sagemakerstudio',
                retention=logs.RetentionDays.ONE_MONTH,
                removal_policy=RemovalPolicy.DESTROY,
            )
            vpc_flow_role = iam.Role(
                self.stack, 'FlowLog',
                assumed_by=iam.ServicePrincipal('vpc-flow-logs.amazonaws.com')
            )
            vpc = ec2.Vpc(
                self.stack,
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
                self.stack, "StudioVPCFlowLog",
                resource_type=ec2.FlowLogResourceType.from_vpc(vpc),
                destination=ec2.FlowLogDestination.to_cloud_watch_logs(log_group, vpc_flow_role)
            )
            # setup security group to be used for sagemaker studio domain
            sagemaker_sg = ec2.SecurityGroup(
                self.stack,
                "SecurityGroup",
                vpc=vpc,
                description="Security Group for SageMaker Studio",
            )

            sagemaker_sg.add_ingress_rule(sagemaker_sg, ec2.Port.all_traffic())
            security_groups = [sagemaker_sg.security_group_id]
            subnet_ids = [private_subnet.subnet_id for private_subnet in vpc.private_subnets]

        vpc_id = vpc.vpc_id

        sagemaker_domain_role = iam.Role(
            self.stack,
            'RoleForSagemakerStudioUsers',
            assumed_by=iam.ServicePrincipal('sagemaker.amazonaws.com'),
            role_name='RoleSagemakerStudioUsers',
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self.stack,
                    id='SagemakerFullAccess',
                    managed_policy_arn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                ),
                iam.ManagedPolicy.from_managed_policy_arn(
                    self.stack, id='S3FullAccess', managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
                ),
            ],
        )

        sagemaker_domain_key = kms.Key(
            self.stack,
            'SagemakerDomainKmsKey',
            alias='SagemakerStudioDomain',
            enable_key_rotation=True,
            admins=[
                iam.ArnPrincipal(self.environment.CDKRoleArn),
                iam.ArnPrincipal(self.environment.EnvironmentDefaultIAMRoleArn),
                sagemaker_domain_role
            ],
            policy=iam.PolicyDocument(
                assign_sids=True,
                statements=[
                    iam.PolicyStatement(
                        actions=[
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey"
                        ],
                        effect=iam.Effect.ALLOW,
                        principals=[
                            iam.ServicePrincipal('sagemaker.amazonaws.com'),
                            iam.ServicePrincipal('elasticfilesystem.amazonaws.com'),
                            iam.ServicePrincipal('ebs.amazonaws.com'),
                            iam.ServicePrincipal('s3.amazonaws.com'),
                            sagemaker_domain_role,
                            iam.ArnPrincipal(self.environment.CDKRoleArn)
                        ] + sagemaker_principals,
                        resources=["*"],
                    )
                ],
            ),
        )

        sagemaker_domain = sagemaker.CfnDomain(
            self.stack,
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
            self.stack,
            'SagemakerStudioDomainId',
            string_value=sagemaker_domain.attr_domain_id,
            parameter_name=f'/dataall/{self.environment.environmentUri}/sagemaker/sagemakerstudio/domain_id',
        )
        return sagemaker_domain


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

        # sm_domain_key = kms.Key.from_lookup(
        #     self, f'SagemakerStudioDomain', alias_name=f"alias/SagemakerStudioDomain"
        # )
        # sm_domain_key.add_to_resource_policy(
        #       iam.PolicyStatement(
        #           sid=f"EnableKeyUsage{env_group.groupUri}",
        #           resources=['*'],
        #           effect=iam.Effect.ALLOW,
        #           principals=[env_group.environmentIAMRoleArn],
        #           actions=[
        #               "kms:Encrypt",
        #               "kms:Decrypt",
        #               "kms:ReEncrypt*",
        #               "kms:GenerateDataKey*",
        #               "kms:DescribeKey"
        #           ],
        #       )
        #   )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)
