from aws_cdk import aws_iam as iam


def create_sagemaker_statements(account: str, region: str, tag_key: str, tag_value: str):
    return [
        iam.PolicyStatement(
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
                    f'aws:ResourceTag/{tag_key}': [tag_value]
                }
            },
        ),
        iam.PolicyStatement(
            actions=['sagemaker:Delete*'],
            resources=[
                f'arn:aws:sagemaker:{region}:{account}:notebook-instance/*',
                f'arn:aws:sagemaker:{region}:{account}:algorithm/*',
                f'arn:aws:sagemaker:{region}:{account}:model/*',
                f'arn:aws:sagemaker:{region}:{account}:endpoint/*',
                f'arn:aws:sagemaker:{region}:{account}:endpoint-config/*',
                f'arn:aws:sagemaker:{region}:{account}:experiment/*',
                f'arn:aws:sagemaker:{region}:{account}:experiment-trial/*',
                f'arn:aws:sagemaker:{region}:{account}:experiment-group/*',
                f'arn:aws:sagemaker:{region}:{account}:model-bias-job-definition/*',
                f'arn:aws:sagemaker:{region}:{account}:model-package/*',
                f'arn:aws:sagemaker:{region}:{account}:model-package-group/*',
                f'arn:aws:sagemaker:{region}:{account}:model-quality-job-definition/*',
                f'arn:aws:sagemaker:{region}:{account}:monitoring-schedule/*',
                f'arn:aws:sagemaker:{region}:{account}:pipeline/*',
                f'arn:aws:sagemaker:{region}:{account}:project/*',
                f'arn:aws:sagemaker:{region}:{account}:app/*'
            ],
            conditions={
                'StringEquals': {
                    f'aws:ResourceTag/{tag_key}': [tag_value]
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
                f'arn:aws:sagemaker:{region}:{account}:notebook-instance/*',
                f'arn:aws:sagemaker:{region}:{account}:monitoring-schedule/*',
                f'arn:aws:sagemaker:{region}:{account}:pipeline/*',
                f'arn:aws:sagemaker:{region}:{account}:training-job/*',
                f'arn:aws:sagemaker:{region}:{account}:processing-job/*',
                f'arn:aws:sagemaker:{region}:{account}:hyper-parameter-tuning-job/*',
                f'arn:aws:sagemaker:{region}:{account}:transform-job/*',
                f'arn:aws:sagemaker:{region}:{account}:automl-job/*'
            ],
            conditions={
                'StringEquals': {
                    f'aws:ResourceTag/{tag_key}': [tag_value]
                }
            },
        ),
        iam.PolicyStatement(
            actions=['sagemaker:Update*'],
            resources=[
                f'arn:aws:sagemaker:{region}:{account}:notebook-instance/*',
                f'arn:aws:sagemaker:{region}:{account}:notebook-instance-lifecycle-config/*',
                f'arn:aws:sagemaker:{region}:{account}:studio-lifecycle-config/*',
                f'arn:aws:sagemaker:{region}:{account}:endpoint/*',
                f'arn:aws:sagemaker:{region}:{account}:pipeline/*',
                f'arn:aws:sagemaker:{region}:{account}:pipeline-execution/*',
                f'arn:aws:sagemaker:{region}:{account}:monitoring-schedule/*',
                f'arn:aws:sagemaker:{region}:{account}:experiment/*',
                f'arn:aws:sagemaker:{region}:{account}:experiment-trial/*',
                f'arn:aws:sagemaker:{region}:{account}:experiment-trial-component/*',
                f'arn:aws:sagemaker:{region}:{account}:model-package/*',
                f'arn:aws:sagemaker:{region}:{account}:training-job/*',
                f'arn:aws:sagemaker:{region}:{account}:project/*'
            ],
            conditions={
                'StringEquals': {
                    f'aws:ResourceTag/{tag_key}': [tag_value]
                }
            },
        ),
        iam.PolicyStatement(
            actions=['sagemaker:InvokeEndpoint', 'sagemaker:InvokeEndpointAsync'],
            resources=[
                f'arn:aws:sagemaker:{region}:{account}:endpoint/*'
            ],
            conditions={
                'StringEquals': {
                    f'aws:ResourceTag/{tag_key}': [tag_value]
                }
            },
        ),
        iam.PolicyStatement(
            actions=[
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents'],
            resources=[
                f'arn:aws:logs:{region}:{account}:log-group:/aws/sagemaker/*',
                f'arn:aws:logs:{region}:{account}:log-group:/aws/sagemaker/*:log-stream:*',
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
