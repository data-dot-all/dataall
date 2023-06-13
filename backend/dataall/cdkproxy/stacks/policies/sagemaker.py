from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Sagemaker(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="SageMakerRead",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:List*',
                    'sagemaker:Describe*',
                    'sagemaker:BatchGet*',
                    'sagemaker:BatchDescribe*',
                    'sagemaker:Search',
                    'sagemaker:RenderUiTemplate',
                    'sagemaker:GetSearchSuggestions',
                    'sagemaker:QueryLineage',
                    'sagemaker:GetSagemakerServicecatalogPortfolioStatus'
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="SageMakerCreateGeneric",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:CreateNotebookInstanceLifecycleConfig',
                    'sagemaker:DeleteNotebookInstanceLifecycleConfig',
                    'sagemaker:CreatePresignedDomainUrl'
                ],
                resources=['*']
            ),
            iam.PolicyStatement(
                sid="SageMakerCreateResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:Create*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:app/{self.resource_prefix}*/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package-group/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint-config/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-group/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:project/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:algorithm/{self.resource_prefix}*',

                ],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                }
            ),
            iam.PolicyStatement(
                sid="SageMakerTagResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:AddTags'],
                resources=['*'],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerDeleteTeamResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:Delete*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:app/{self.resource_prefix}*/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package-group/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint-config/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-group/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:project/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:algorithm/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerStartStopTeamResources",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:Start*',
                    'sagemaker:Stop*'
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:training-job/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:processing-job/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:hyper-parameter-tuning-job/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:transform-job/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:automl-job/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerUpdateTeamResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:Update*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:app/{self.resource_prefix}*/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance-lifecycle-config/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:studio-lifecycle-config/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/{self.resource_prefix}*/execution/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial-component/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:training-job/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:project/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerTeamEndpoints",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:InvokeEndpoint',
                    'sagemaker:InvokeEndpointAsync'
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerLogging",
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents'],
                resources=[
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*',
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*:log-stream:*',
                ]
            ),
            iam.PolicyStatement(
                sid="SageMakerReadECR",
                effect=iam.Effect.ALLOW,
                actions=[
                    'ecr:GetAuthorizationToken',
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchGetImage'
                ],
                resources=[
                    '*'
                ]
            )
        ]
        return statements
