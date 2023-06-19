from .service_policy import ServicePolicy
from aws_cdk import aws_iam as iam


class AwsCICD(ServicePolicy):
    """
    Class including all permissions needed to work with AWS CICD services: CodeCommit, CodePipeline and CodeBuild.
    It allows data.all users to:
    - Create and manage CodeBuild, CodeCommit and CodePipeline resources for the team
    - Create an S3 Bucket for codepipeline prefixed by "codepipeline-"
    - Read/Write to and from S3 Buckets prefixed by "codepipeline-"
    """
    def get_statements(self):
        statements = [
            iam.PolicyStatement(
                sid="GenericCodeCommit",
                actions=[
                    'codecommit:List*',
                    'codecommit:CreateApprovalRuleTemplate',
                    'codecommit:UpdateApprovalRuleTemplateName',
                    'codecommit:GetApprovalRuleTemplate',
                    'codecommit:ListApprovalRuleTemplates',
                    'codecommit:DeleteApprovalRuleTemplate',
                    'codecommit:UpdateApprovalRuleTemplateContent',
                    'codecommit:UpdateApprovalRuleTemplateDescription',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="TagCodecommitTeamRepo",
                actions=[
                    "codecommit:TagResource"
                ],
                resources=[
                    f'arn:aws:codecommit:{self.region}:{self.account}:{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                sid="AllCodecommitTeamRepo",
                actions=[
                    "codecommit:AssociateApprovalRuleTemplateWithRepository",
                    "codecommit:Batch*",
                    "codecommit:CancelUploadArchive",
                    "codecommit:Create*",
                    "codecommit:Delete*",
                    "codecommit:Describe*",
                    "codecommit:DisassociateApprovalRuleTemplateFromRepository",
                    "codecommit:EvaluatePullRequestApprovalRules",
                    "codecommit:Get*",
                    "codecommit:Git*",
                    "codecommit:List*",
                    "codecommit:Merge*",
                    "codecommit:OverridePullRequestApprovalRules",
                    "codecommit:Post*",
                    "codecommit:Put*",
                    "codecommit:TestRepositoryTriggers",
                    "codecommit:Update*",
                    "codecommit:UploadArchive",
                ],
                resources=[
                    f'arn:aws:codecommit:{self.region}:{self.account}:{self.resource_prefix}*'
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value],
                    },
                },
            ),
            iam.PolicyStatement(
                sid="GenericCodePipeline",
                actions=[
                    'codepipeline:AcknowledgeJob',
                    'codepipeline:AcknowledgeThirdPartyJob',
                    'codepipeline:GetThirdPartyJobDetails',
                    'codepipeline:GetJobDetails',
                    'codepipeline:GetActionType',
                    'codepipeline:ListActionTypes',
                    'codepipeline:ListPipelines',
                    'codepipeline:PollForThirdPartyJobs',
                    'codepipeline:PutThirdPartyJobSuccessResult',
                    'codepipeline:PutThirdPartyJobFailureResult',
                    'codepipeline:PutJobFailureResult',
                    'codepipeline:PutJobSuccessResult',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="TagCodepipelineTeamRepo",
                actions=['codepipeline:TagResource'],
                resources=[
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:actiontype:/*/*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:webhook:{self.resource_prefix}',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="AllCodepipelineTeamRepo",
                actions=[
                    'codepipeline:Create*',
                    'codepipeline:Delete*',
                    'codepipeline:DeregisterWebhookWithThirdParty',
                    'codepipeline:DisableStageTransition',
                    'codepipeline:EnableStageTransition',
                    'codepipeline:Get*',
                    'codepipeline:List*',
                    'codepipeline:PollForJobs',
                    'codepipeline:Put*',
                    'codepipeline:RegisterWebhookWithThirdParty',
                    'codepipeline:RetryStageExecution',
                    'codepipeline:StartPipelineExecution',
                    'codepipeline:StopPipelineExecution',
                    'codepipeline:Update*',
                ],
                resources=[
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*/*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:actiontype:/*/*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:{self.resource_prefix}*/*',
                    f'arn:aws:codepipeline:{self.region}:{self.account}:webhook:{self.resource_prefix}',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="CodePipelineCreateS3Bucket",
                effect=iam.Effect.ALLOW,
                actions=[
                    's3:CreateBucket',
                    's3:ListBucket',
                    's3:PutBucketPublicAccessBlock'
                ],
                resources=["arn:aws:s3:::codepipeline-*"],
            ),
            iam.PolicyStatement(
                sid="CodePipelineReadWriteS3Bucket",
                actions=[
                    's3:GetObject',
                    's3:PutObject',
                    's3:DeleteObject'
                ],
                effect=iam.Effect.ALLOW,
                resources=[
                    'arn:aws:s3:::codepipeline-*/*',
                ],
            ),
            iam.PolicyStatement(
                sid="GenericCodeBuild",
                actions=[
                    'codebuild:ListCuratedEnvironmentImages',
                    'codebuild:ListReportGroups',
                    'codebuild:ListSourceCredentials',
                    'codebuild:ListRepositories',
                    'codebuild:ListSharedProjects',
                    'codebuild:ListBuildBatches',
                    'codebuild:ListSharedReportGroups',
                    'codebuild:ImportSourceCredentials',
                    'codebuild:ListReports',
                    'codebuild:ListBuilds',
                    'codebuild:DeleteOAuthToken',
                    'codebuild:ListProjects',
                    'codebuild:DeleteSourceCredentials',
                    'codebuild:PersistOAuthToken',
                    'codebuild:ListConnectedOAuthAccounts',
                ],
                resources=['*'],
            ),
            iam.PolicyStatement(
                sid="TagCodebuildTeamRepo",
                actions=[
                    'codebuild:CreateProject',
                    'codebuild:UpdateProject',
                    'codebuild:UpdateProjectVisibility',
                    'codebuild:CreateReportGroup',
                    'codebuild:UpdateReportGroup',
                ],
                resources=[
                    f'arn:aws:codebuild:{self.region}:{self.account}:project/{self.resource_prefix}*',
                    f'arn:aws:codebuild:{self.region}:{self.account}:report-group/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:RequestTag/{self.tag_key}': [self.tag_value]
                    }
                },
            ),
            iam.PolicyStatement(
                sid="AllCodebuildTeamRepo",
                actions=[
                    'codebuild:Batch*',
                    'codebuild:CreateReport',
                    'codebuild:CreateWebhoook',
                    'codebuild:Delete*',
                    'codebuild:Describe*',
                    'codebuild:Get*',
                    'codebuild:InvalidateProjectCache',
                    'codebuild:List*',
                    'codebuild:PutResourcePolicy',
                    'codebuild:Retry*',
                    'codebuild:Start*',
                    'codebuild:Stop*',
                    'codebuild:UpdateReport',
                    'codebuild:UpdateWebhook',
                ],
                resources=[
                    f'arn:aws:codebuild:{self.region}:{self.account}:project/{self.resource_prefix}*',
                    f'arn:aws:codebuild:{self.region}:{self.account}:report-group/{self.resource_prefix}*',
                ],
                conditions={
                    'StringEquals': {
                        f'aws:ResourceTag/{self.tag_key}': [self.tag_value]
                    }
                },
            )
        ]
        return statements
