from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Sagemaker(ServicePolicy):
    """
    Class including all permissions needed to work with Amazon SageMaker.
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="SageMakerTagResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:AddTags'],
                resources=['*'],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
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
            # SageMaker Notebooks permissions
            iam.PolicyStatement(
                sid="SageMakerCreateTaggedResourcesNotebooks",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreateNotebookInstance'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',

                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerNotebookInstanceLifecycleConfig",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:CreateNotebookInstanceLifecycleConfig',
                    'sagemaker:DeleteNotebookInstanceLifecycleConfig',
                ],
                resources=['*']
            ),
            iam.PolicyStatement(
                sid="SageMakerCreatePresignedNotebookInstanceUrl",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreatePresignedNotebookInstanceUrl'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'sagemaker:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerManageResourcesNotebooks",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:DeleteNotebookInstance',
                    'sagemaker:UpdateNotebookInstance',
                    'sagemaker:StartNotebookInstance',
                    'sagemaker:StopNotebookInstance'
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                },
            ),
            # SageMaker Studio permissions
            iam.PolicyStatement(
                sid="SageMakerApps",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:CreateApp',
                    'sagemaker:DeleteApp'
                ],
                resources=[f'arn:aws:sagemaker:{self.region}:{self.account}:app/*/*']
            ),
            iam.PolicyStatement(
                sid="SageMakerCreatePresignedDomainUrl",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreatePresignedDomainUrl'],
                resources=[f'arn:aws:sagemaker:{self.region}:{self.account}:user-profile/*/*'],
                conditions={
                    'StringEquals': {
                        f'sagemaker:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerManageTeamResourcesMLStudio",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:DeleteDomain',
                    'sagemaker:DeleteUserProfile',
                    'sagemaker:UpdateDomain',
                    'sagemaker:UpdateUserProfile',
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:user-profile/*/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="SageMakerCreateTaggedGenericResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:Create*'],
                not_resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:user-profile/*/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:app/*/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    },
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            #processing job
            # model registry
            # use one of the project templates
            iam.PolicyStatement(
                sid="SageMakerManageTeamResources",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:Delete*',
                    'sagemaker:Update*'
                ],
                not_resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:user-profile/*/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:app/*/*',
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
                sid="SageMakerReadServiceCatalog",
                effect=iam.Effect.ALLOW,
                actions=[
                    'servicecatalog:ListAcceptedPortfolioShares',
                    'servicecatalog:ListPrincipalsForPortfolio',
                ],
                resources=['*']
            ),
            # Logging and ECR support permissions
            iam.PolicyStatement(
                sid="SageMakerLogging",
                effect=iam.Effect.ALLOW,
                actions=[
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents'
                ],
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
                resources=['*']
            )
        ]
        return statements
