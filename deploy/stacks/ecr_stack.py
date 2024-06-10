from aws_cdk import (
    aws_ecr as ecr,
    aws_iam as iam,
    aws_ssm as ssm,
    Stack,
    RemovalPolicy,
)


class ECRRepositoryStack(Stack):
    def __init__(
        self,
        scope,
        id,
        target_envs: [str] = None,
        envname='dev',
        resource_prefix='dataall',
        repository_name=None,
        **kwargs,
    ):
        super().__init__(scope, id, **kwargs)

        repo = ecr.Repository(
            self,
            'ECRRepository',
            repository_name=repository_name,
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            encryption=ecr.RepositoryEncryption.KMS,
            image_tag_mutability=ecr.TagMutability.IMMUTABLE,
        )

        repo.add_lifecycle_rule(max_image_count=200)
        if target_envs:
            principals: [iam.AccountPrincipal] = [iam.AccountPrincipal(account['account']) for account in target_envs]
            repo.add_to_resource_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:ListImages',
                        'ecr:BatchGetImage',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:GetAuthorizationToken',
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:BatchGetImage',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:PutImage',
                        'ecr:InitiateLayerUpload',
                        'ecr:UploadLayerPart',
                        'ecr:CompleteLayerUpload',
                    ],
                    principals=principals,
                )
            )

            repo.add_to_resource_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:BatchGetImage',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:GetAuthorizationToken',
                    ],
                    principals=[
                        iam.ServicePrincipal(service='ecs.amazonaws.com'),
                        iam.ServicePrincipal(service='ecs-tasks.amazonaws.com'),
                        iam.ServicePrincipal(service='codebuild.amazonaws.com'),
                        iam.ServicePrincipal(service='lambda.amazonaws.com'),
                    ],
                )
            )

            repo.add_to_resource_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'ecr:GetDownloadUrlForLayer',
                        'ecr:BatchGetImage',
                        'ecr:BatchCheckLayerAvailability',
                        'ecr:PutImage',
                        'ecr:InitiateLayerUpload',
                        'ecr:UploadLayerPart',
                        'ecr:CompleteLayerUpload',
                    ],
                    principals=[iam.AccountPrincipal(account_id=self.account)],
                )
            )

        ssm.StringParameter(
            self,
            'ECRRepoUriParam',
            parameter_name=f'/dataall/{envname}/ecr/repository_uri',
            string_value=repo.repository_uri,
        )

        ssm.StringParameter(
            self,
            'ECRRepoNameParam',
            parameter_name=f'/dataall/{envname}/ecr/repository_name',
            string_value=repo.repository_name,
        )

        self.ecr_repo = repo

        regions = [env['region'] for env in target_envs]
        regions.append(self.region)

        regions = list(set(regions))
        if len(regions) > 1:
            regions.remove(self.region)
            replication_destinations = []
            for region in regions:
                replication_destinations.append(
                    ecr.CfnReplicationConfiguration.ReplicationDestinationProperty(
                        region=region, registry_id=self.account
                    )
                )
            ecr.CfnReplicationConfiguration(
                self,
                'MyCfnReplicationConfiguration',
                replication_configuration=ecr.CfnReplicationConfiguration.ReplicationConfigurationProperty(
                    rules=[
                        ecr.CfnReplicationConfiguration.ReplicationRuleProperty(
                            destinations=replication_destinations,
                        )
                    ]
                ),
            )
