from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class Sagemaker(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                actions=[
                    'sagemaker:List*',
                    'sagemaker:Describe*',
                    'sagemaker:BatchGet*',
                    'sagemaker:BatchDescribe*',
                    'sagemaker:Search',
                    'sagemaker:RenderUiTemplate',
                    'sagemaker:GetSearchSuggestions',
                    'sagemaker:QueryLineage',
                    'sagemaker:CreateNotebookInstanceLifecycleConfig',
                    'sagemaker:DeleteNotebookInstanceLifecycleConfig',
                    'sagemaker:CreatePresignedDomainUrl'
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                actions=['sagemaker:AddTags'],
                resources=['*'],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                actions=['sagemaker:Delete*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:algorithm/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint-config/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-group/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-bias-job-definition/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package-group/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-quality-job-definition/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:project/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:app/*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                actions=['sagemaker:CreateApp'],
                resources=['*']
            ),
            iam.PolicyStatement(
                actions=['sagemaker:Create*'],
                resources=['*'],
            ),
            iam.PolicyStatement(
                actions=['sagemaker:Start*', 'sagemaker:Stop*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:training-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:processing-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:hyper-parameter-tuning-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:transform-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:automl-job/*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                actions=['sagemaker:Update*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance-lifecycle-config/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:studio-lifecycle-config/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:pipeline-execution/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:monitoring-schedule/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:experiment-trial-component/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:model-package/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:training-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:project/*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                actions=['sagemaker:InvokeEndpoint', 'sagemaker:InvokeEndpointAsync'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
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
                actions=[
                    'ecr:GetAuthorizationToken',
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchGetImage'],
                resources=[
                    '*'
                ]
            )
        ]
        return statements
