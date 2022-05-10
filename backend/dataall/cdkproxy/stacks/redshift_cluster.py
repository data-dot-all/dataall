import json
import logging
import os

from aws_cdk import (
    aws_ec2 as ec2,
    aws_redshift_alpha as redshift,
    aws_ec2,
    aws_kms,
    aws_secretsmanager,
    aws_iam,
    aws_s3,
    RemovalPolicy,
    Duration,
    Stack,
)
from aws_cdk.aws_secretsmanager import SecretStringGenerator

from .manager import stack
from ... import db
from ...db import models
from ...db.api import Environment
from ...utils.cdk_nag_utils import CDKNagUtil
from ...utils.runtime_stacks_tagging import TagsUtil

logger = logging.getLogger(__name__)


@stack(stack="redshift")
class RedshiftStack(Stack):
    module_name = __file__

    def get_engine(self) -> db.Engine:
        return db.get_engine(envname=os.environ.get("envname", "local"))

    def get_target(self, target_uri):
        engine = self.get_engine()
        with engine.scoped_session() as session:
            cluster: models.RedshiftCluster = session.query(models.RedshiftCluster).get(target_uri)
            environment: models.Environment = session.query(models.Environment).get(cluster.environmentUri)
        return cluster, environment

    def get_env_group(self, cluster: models.RedshiftCluster) -> models.EnvironmentGroup:
        engine = self.get_engine()
        with engine.scoped_session() as session:
            env = Environment.get_environment_group(session, cluster.SamlGroupName, cluster.environmentUri)
        return env

    def __init__(self, scope, id: str, target_uri: str = None, **kwargs) -> None:
        super().__init__(scope,
                         id,
                         description="Cloud formation stack of REDSHIFT CLUSTER: {}; URI: {}; DESCRIPTION: {}".format(
                             self.get_target(target_uri=target_uri)[0].label,
                             target_uri,
                             self.get_target(target_uri=target_uri)[0].description,
                         )[:1024],
                         **kwargs)

        # Required for dynamic stack tagging
        self.target_uri = target_uri

        cluster, environment = self.get_target(target_uri=target_uri)

        env_group = self.get_env_group(cluster)

        if not cluster.imported:
            vpc = aws_ec2.Vpc.from_lookup(self, "vpcRedshiftcluster", vpc_id=cluster.vpc)

            security_group = aws_ec2.SecurityGroup(
                self,
                f"sg{cluster.name}",
                vpc=vpc,
                allow_all_outbound=True,
                security_group_name=cluster.name,
            )

            key = aws_kms.Key(
                self,
                f"key{cluster.name}",
                removal_policy=RemovalPolicy.RETAIN,
                alias=f"{cluster.name}",
                enable_key_rotation=True,
            )

            cluster_parameter_group = redshift.ClusterParameterGroup(
                self,
                "RedshiftClusterParameterGroup",
                description=f"{cluster.name} parameter group",
                parameters={
                    "enable_user_activity_logging": "true",
                    "require_ssl": "true",
                },
            )

            cluster_subnet_group = redshift.ClusterSubnetGroup(
                self,
                cluster.name,
                description=f"Redshift Cluster {cluster.name} subnet group",
                vpc=vpc,
                removal_policy=RemovalPolicy.DESTROY,
            )

            master_secret = redshift.DatabaseSecret(
                self,
                f"{environment.resourcePrefix}-msredshift-{cluster.clusterUri}"[:23],
                username=cluster.masterUsername,
            )
            master_secret.add_rotation_schedule(
                id="msRot",
                automatically_after=Duration.days(90),
                hosted_rotation=aws_secretsmanager.HostedRotation.redshift_single_user(),
            )
            redshift_login = redshift.Login(
                master_username=master_secret.secret_value_from_json("username").to_string(),
                master_password=master_secret.secret_value_from_json("password"),
            )
            redshift_role = aws_iam.Role.from_role_arn(self, "RedshiftRole", role_arn=env_group.environmentIAMRoleArn)
            redshift_cluster = redshift.Cluster(
                self,
                "RedshiftCluster",
                cluster_name=cluster.name,
                master_user=redshift_login,
                vpc=vpc,
                default_database_name=cluster.masterDatabaseName,
                cluster_type=redshift.ClusterType.SINGLE_NODE
                if cluster.numberOfNodes == 1
                else redshift.ClusterType.MULTI_NODE,
                number_of_nodes=None if cluster.numberOfNodes == 1 else cluster.numberOfNodes,
                node_type=redshift.NodeType(cluster.nodeType.replace(".", "_").upper()),
                port=cluster.port,
                roles=[redshift_role],
                publicly_accessible=False,
                encrypted=True,
                encryption_key=key,
                parameter_group=cluster_parameter_group,
                security_groups=[
                    security_group,
                ],
                subnet_group=cluster_subnet_group,
                logging_bucket=aws_s3.Bucket.from_bucket_name(
                    self,
                    "EnvLoggingBucket",
                    f"{environment.EnvironmentDefaultBucketName}",
                ),
                logging_key_prefix=f"redshift_logs/{cluster.name}/",
            )

        else:
            redshift.Cluster.from_cluster_attributes(
                self,
                "ImportedRedshiftCluster",
                cluster_name=cluster.name,
                cluster_endpoint_address=cluster.endpoint,
                cluster_endpoint_port=cluster.port,
            )

        dh_user_secret = aws_secretsmanager.Secret(
            self,
            "UserSecret",
            secret_name=cluster.datahubSecret,
            generate_secret_string=SecretStringGenerator(
                secret_string_template=json.dumps({"username": cluster.databaseUser}),
                generate_string_key="password",
                exclude_punctuation=True,
            ),
        )
        dh_user_secret.add_rotation_schedule(
            id="rt",
            automatically_after=Duration.days(90),
            hosted_rotation=aws_secretsmanager.HostedRotation.redshift_single_user(),
        )

        TagsUtil.add_tags(self)

        CDKNagUtil.check_rules(self)
