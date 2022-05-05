from aws_cdk import aws_iam as iam

from .service_policy import ServicePolicy


class Sagemaker(ServicePolicy):
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                actions=[
                    'sagemaker:List*',
                    'sagemaker:Describe*',
                    'sagemaker:Search',
                    'sagemaker:GetSearchSuggestions',
                    'sagemaker:CreateNotebookInstanceLifecycleConfig',
                    'sagemaker:DeleteNotebookInstanceLifecycleConfig',
                    'sagemaker:CreatePresignedDomainUrl',
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
                    f'arn:aws:sagemaker:{self.region}:{self.account}:training-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint-config/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                actions=['sagemaker:Create*'],
                resources=['*'],
                conditions={
                    'StringEquals': {f'aws:RequestTag/{self.tag_key}': [self.tag_value]}
                },
            ),
            iam.PolicyStatement(
                actions=['sagemaker:Start*', 'sagemaker:Stop*'],
                resources=[
                    f'arn:aws:sagemaker:{self.region}:{self.account}:notebook-instance/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:training-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:processing-job/*',
                    f'arn:aws:sagemaker:{self.region}:{self.account}:hyper-parameter-tuning-job/*',
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
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/*',
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
                    f'arn:aws:sagemaker:{self.region}:{self.account}:endpoint/*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
        ]
        return statements
