from aws_cdk import aws_iam as iam

from dataall.core.environment.cdk.env_role_core_policies.service_policy import ServicePolicy
from dataall.modules.notebooks.services.notebook_permissions import CREATE_NOTEBOOK


class SagemakernotebookPolicy(ServicePolicy):
    """
    Class including all permissions needed to work with Amazon SageMaker.
    - Allow creation and management of SageMaker Notebooks only if tagged with team tag
    - DO NOT allow creation of domain because this is handled in the environment stack
    - DO NOT allow creation of user-profiles because this is handled in the ML Studio stack
    - Allow management of domains and user-profiles tagged with team tag
    - Allow any action besides the above listed ones on resources that are not notebooks, domains, apps and user-profiles
    - Allow support permissions on ECR, Service Catalog and logging
    """

    # TODO (in cleanup tasks): Remove those policies that are only needed for SM studio, right now we have both
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_NOTEBOOK not in group_permissions:
            return []

        return [
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:AddTags'],
                resources=['*'],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:List*',
                    'sagemaker:List*',
                    'sagemaker:Describe*',
                    'sagemaker:BatchGet*',
                    'sagemaker:BatchDescribe*',
                    'sagemaker:Search',
                    'sagemaker:RenderUiTemplate',
                    'sagemaker:GetSearchSuggestions',
                    'sagemaker:QueryLineage',
                    'sagemaker:GetSagemakerServicecatalogPortfolioStatus',
                    'sagemaker:CreateNotebookInstanceLifecycleConfig',
                    'sagemaker:DeleteNotebookInstanceLifecycleConfig',
                ],
                resources=['*'],
            ),
            # SageMaker Notebooks permissions
            iam.PolicyStatement(
                # sid="SageMakerCreateTaggedResourcesNotebooks",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreateNotebookInstance'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                # sid="SageMakerCreatePresignedNotebookInstanceUrl",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreatePresignedNotebookInstanceUrl'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {f'sagemaker:ResourceTag/{self.tag_key}': [self.tag_value]},
                },
            ),
            iam.PolicyStatement(
                # sid="SageMakerManageResourcesNotebooks",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:*NotebookInstance',
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]},
                },
            ),
            # SageMaker Studio permissions
            iam.PolicyStatement(
                # sid="SageMakerManageTeamResourcesMLStudio",
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
                conditions={'StringEquals': {f'aws:ResourceTag/{self.tag_key}': [self.tag_value]}},
            ),
            # For everything that is not domains and user-profiles we allow permissions if the resource is tagged
            # Deny on creation of domains and users, generic allow for prefixed and tagged resources
            # allow for apps (cannot be tagged) and special tag needed for CreatePresignedDomainUrl
            iam.PolicyStatement(
                # sid="SageMakerDenyCreateDomainsUsers",
                effect=iam.Effect.DENY,
                actions=[
                    'sagemaker:CreateDomain',
                    'sagemaker:CreateUserProfile',
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:domain/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:user-profile/*/*',
                ],
            ),
            iam.PolicyStatement(
                # sid="SageMakerCreateGenericResources",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:Create*'],
                not_resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:*/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:*/{self.resource_prefix}*/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                # sid="SageMakerApps",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreateApp', 'sagemaker:DeleteApp'],
                resources=[f'arn:aws:sagemaker:{self.region}:{self.account}:app/*/*'],
            ),
            iam.PolicyStatement(
                # sid="SageMakerCreatePresignedDomainUrl",
                effect=iam.Effect.ALLOW,
                actions=['sagemaker:CreatePresignedDomainUrl'],
                resources=[f'arn:aws:sagemaker:{self.region}:{self.account}:user-profile/*/*'],
                conditions={
                    'StringEquals': {f'sagemaker:ResourceTag/{self.tag_key}': [self.tag_value]},
                },
            ),
            iam.PolicyStatement(
                # sid="SageMakerManageGenericResources",
                effect=iam.Effect.ALLOW,
                actions=[
                    'sagemaker:Delete*',
                    'sagemaker:Update*',
                    'sagemaker:Start*',
                    'sagemaker:Stop*',
                    'sagemaker:InvokeEndpoint',
                    'sagemaker:InvokeEndpointAsync',
                ],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:*/{self.resource_prefix}*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:*/{self.resource_prefix}*/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            # Logging and support permissions
            iam.PolicyStatement(
                # sid="SageMakerLogging",
                effect=iam.Effect.ALLOW,
                actions=['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
                resources=[
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*',
                    f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/sagemaker/*:log-stream:*',
                ],
            ),
            iam.PolicyStatement(
                # sid="SageMakerSupport",
                effect=iam.Effect.ALLOW,
                actions=[
                    'ecr:GetAuthorizationToken',
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchGetImage',
                    'servicecatalog:ListAcceptedPortfolioShares',
                    'servicecatalog:ListPrincipalsForPortfolio',
                ],
                resources=['*'],
            ),
        ]
