from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam
)

class dataAllBaseInfra(Stack):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Data.All IAM PivotRole creation
        self.create_dataall_role(name="dataallPivotRole", principal_id=config.DATAALL_ACCOUNT, external_id=config.EXTERNAL_ID, env_resource_prefix=config.RESOURCE_PREFIX)

        # Data.All IAM Lake Formation service role creation
        self.lf_service_role = iam.CfnServiceLinkedRole(self, "LakeFormationSLR",
                                                        aws_service_name="lakeformation.amazonaws.com"
                                                        )

    def create_dataall_role(self, name: str, principal_id: str, external_id: str,
                            env_resource_prefix: str) -> iam.Role:
        """
        Creates an IAM Role that will enable data.all to interact with this Data Account

        :param str name: Role name
        :param str principal_id: AWS Account ID of central data.all
        :param str external_id: External ID provided by data.all
        :param str env_resource_prefix: Environment Resource Prefix provided by data.all
        :returns: Created IAM Role
        :rtype: iam.Role
        """

        role = iam.Role(self, "DataAllPivotRole",
                        role_name=name,
                        assumed_by=iam.CompositePrincipal(
                            iam.ServicePrincipal("glue.amazonaws.com"),
                            iam.ServicePrincipal("lakeformation.amazonaws.com"),
                            iam.ServicePrincipal("lambda.amazonaws.com")
                        ),
                        path="/",
                        max_session_duration=Duration.hours(12),
                        managed_policies=[
                            self._create_dataall_policy0(env_resource_prefix),
                            self._create_dataall_policy1(env_resource_prefix),
                            self._create_dataall_policy2(env_resource_prefix),
                            self._create_dataall_policy3(env_resource_prefix, name)
                        ]
                        )

        role.assume_role_policy.add_statements(iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[
                        iam.AccountPrincipal(account_id=principal_id)
                    ],
                    actions=["sts:AssumeRole"],
                    conditions={"StringEquals": {"sts:ExternalId": external_id}}
                ))


        return role

    def _create_dataall_policy0(self, env_resource_prefix: str) -> iam.ManagedPolicy:
        """
        Creates the first managed IAM Policy required for the Pivot Role used by data.all

        :param str env_resource_prefix: Environment Resource Prefix provided by data.all
        :returns: Created IAM Policy
        :rtype: iam.ManagedPolicy
        """
        return iam.ManagedPolicy(self, "PivotRolePolicy0",
                                 managed_policy_name=f"{env_resource_prefix}-pivotrole-policy-0",
                                 statements=[
                                     # Athena permissions
                                     iam.PolicyStatement(
                                         sid="Athena", effect=iam.Effect.ALLOW, resources=["*"],
                                         actions=[
                                             "athena:GetQuery*",
                                             "athena:StartQueryExecution",
                                             "athena:ListWorkGroups"
                                         ]
                                     ),
                                     # Athena Workgroups permissions
                                     iam.PolicyStatement(
                                         sid="AthenaWorkgroups", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "athena:GetWorkGroup",
                                             "athena:CreateWorkGroup",
                                             "athena:UpdateWorkGroup",
                                             "athena:DeleteWorkGroup",
                                             "athena:TagResource",
                                             "athena:UntagResource",
                                             "athena:ListTagsForResource"
                                         ],
                                         resources=[
                                             f"arn:aws:athena:*:{self.account}:workgroup/{env_resource_prefix}*"]
                                     ),
                                     # AWS Glue Crawler Bucket
                                     iam.PolicyStatement(
                                         sid="AwsGlueCrawlerBucket", effect=iam.Effect.ALLOW,
                                         actions=["s3:GetObject"],
                                         resources=["arn:aws:s3:::crawler-public*"]
                                     ),
                                     # S3 Access points
                                     iam.PolicyStatement(
                                         sid="ManagedAccessPoints", effect=iam.Effect.ALLOW,
                                         actions=[
                                            "s3:GetAccessPoint",
                                            "s3:GetAccessPointPolicy",
                                            "s3:ListAccessPoints",
                                            "s3:CreateAccessPoint",
                                            "s3:DeleteAccessPoint",
                                            "s3:GetAccessPointPolicyStatus",
                                            "s3:DeleteAccessPointPolicy",
                                            "s3:PutAccessPointPolicy"
                                         ],
                                         resources=[f"arn:aws:s3:*:{self.account}:accesspoint/*"]
                                     ),
                                     # S3 Managed Buckets
                                     iam.PolicyStatement(
                                         sid="ManagedBuckets", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "s3:List*",
                                             "s3:Delete*",
                                             "s3:Get*",
                                             "s3:Put*"
                                         ],
                                         resources=[f"arn:aws:s3:::{env_resource_prefix}*"]
                                     ),
                                     # S3 Imported Buckets
                                     iam.PolicyStatement(
                                         sid="ImportedBuckets", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "s3:List*",
                                             "s3:GetBucket*",
                                             "s3:GetLifecycleConfiguration",
                                             "s3:GetObject",
                                             "s3:PutBucketPolicy",
                                             "s3:PutBucketTagging",
                                             "s3:PutObject",
                                             "s3:PutObjectAcl",
                                             "s3:PutBucketOwnershipControls"
                                         ],
                                         resources=["arn:aws:s3:::*"]
                                     ),
                                     # AWS Logging Buckets
                                     iam.PolicyStatement(
                                         sid="AWSLoggingBuckets", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "s3:PutBucketAcl",
                                             "s3:PutBucketNotification"
                                         ],
                                         resources=[f"arn:aws:s3:::{env_resource_prefix}-logging-*"]
                                     ),
                                     # Read Buckets
                                     iam.PolicyStatement(
                                         sid="ReadBuckets", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "s3:ListAllMyBuckets",
                                             "s3:GetBucketLocation",
                                             "s3:PutBucketTagging"
                                         ],
                                         resources=["*"]
                                     ),
                                     # CloudWatch Metrics
                                     iam.PolicyStatement(
                                         sid="CWMetrics", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "cloudwatch:PutMetricData",
                                             "cloudwatch:GetMetricData",
                                             "cloudwatch:GetMetricStatistics"
                                         ],
                                         resources=["*"]
                                     ),
                                     # Logs
                                     iam.PolicyStatement(
                                         sid="Logs", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "logs:CreateLogGroup",
                                             "logs:CreateLogStream",
                                             "logs:PutLogEvents"
                                         ],
                                         resources=[
                                             f"arn:aws:logs:*:{self.account}:/aws-glue/*",
                                             f"arn:aws:logs:*:{self.account}:/aws-lambda/*",
                                             f"arn:aws:logs:*:{self.account}:/{env_resource_prefix}*"
                                         ]
                                     ),
                                     # Logging
                                     iam.PolicyStatement(
                                         sid="Logging", effect=iam.Effect.ALLOW,
                                         actions=["logs:PutLogEvents"],
                                         resources=["*"]
                                     ),
                                     # EventBridge (CloudWatch Events)
                                     iam.PolicyStatement(
                                         sid="CWEvents", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "events:DeleteRule",
                                             "events:List*",
                                             "events:PutRule",
                                             "events:PutTargets",
                                             "events:RemoveTargets"
                                         ],
                                         resources=["*"]
                                     ),
                                     # Glue
                                     iam.PolicyStatement(
                                         sid="Glue", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "glue:BatchCreatePartition",
                                             "glue:BatchDeletePartition",
                                             "glue:BatchDeleteTable",
                                             "glue:CreateCrawler",
                                             "glue:CreateDatabase",
                                             "glue:CreatePartition",
                                             "glue:CreateTable",
                                             "glue:DeleteCrawler",
                                             "glue:DeleteDatabase",
                                             "glue:DeleteJob",
                                             "glue:DeletePartition",
                                             "glue:DeleteTable",
                                             "glue:DeleteTrigger",
                                             "glue:BatchGet*",
                                             "glue:Get*",
                                             "glue:List*",
                                             "glue:StartCrawler",
                                             "glue:StartJobRun",
                                             "glue:StartTrigger",
                                             "glue:SearchTables",
                                             "glue:UpdateDatabase",
                                             "glue:UpdatePartition",
                                             "glue:UpdateTable",
                                             "glue:UpdateTrigger",
                                             "glue:UpdateJob",
                                             "glue:TagResource",
                                             "glue:UpdateCrawler"
                                         ],
                                         resources=["*"]
                                     ),
                                     # KMS
                                     iam.PolicyStatement(
                                         sid="KMS", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "kms:Decrypt",
                                             "kms:Encrypt",
                                             "kms:GenerateDataKey*",
                                             "kms:PutKeyPolicy",
                                             "kms:ReEncrypt*",
                                             "kms:TagResource",
                                             "kms:UntagResource"
                                         ],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="KMSAlias", effect=iam.Effect.ALLOW,
                                         actions=["kms:DeleteAlias"],
                                         resources=[f"arn:aws:kms:*:{self.account}:alias/{env_resource_prefix}*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="KMSCreate", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "kms:List*",
                                             "kms:DescribeKey",
                                             "kms:CreateAlias",
                                             "kms:CreateKey"
                                         ],
                                         resources=["*"]
                                     ),
                                     # AWS Organizations
                                     iam.PolicyStatement(
                                         sid="Organizations", effect=iam.Effect.ALLOW,
                                         actions=["organizations:DescribeOrganization"],
                                         resources=["*"]
                                     ),
                                     # Resource Tags
                                     iam.PolicyStatement(
                                         sid="ResourceGroupTags", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "tag:*",
                                             "resource-groups:*"
                                         ],
                                         resources=["*"]
                                     ),
                                     # SNS
                                     iam.PolicyStatement(
                                         sid="SNSPublish", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "sns:Publish",
                                             "sns:SetTopicAttributes",
                                             "sns:GetTopicAttributes",
                                             "sns:DeleteTopic",
                                             "sns:Subscribe",
                                             "sns:TagResource",
                                             "sns:UntagResource",
                                             "sns:CreateTopic"
                                         ],
                                         resources=[f"arn:aws:sns:*:{self.account}:{env_resource_prefix}*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="SNSList", effect=iam.Effect.ALLOW,
                                         actions=["sns:ListTopics"],
                                         resources=["*"]
                                     ),
                                     # SQS
                                     iam.PolicyStatement(
                                         sid="SQSList", effect=iam.Effect.ALLOW,
                                         actions=["sqs:ListQueues"],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="SQS", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "sqs:ReceiveMessage",
                                             "sqs:SendMessage"
                                         ],
                                         resources=[f"arn:aws:sqs:*:{self.account}:{env_resource_prefix}*"]
                                     )
                                 ]
                                 )

    def _create_dataall_policy1(self, env_resource_prefix: str) -> iam.ManagedPolicy:
        """
        Creates the second managed IAM Policy required for the Pivot Role used by data.all

        :param str env_resource_prefix: Environment Resource Prefix provided by data.all
        :returns: Created IAM Policy
        :rtype: iam.ManagedPolicy
        """
        return iam.ManagedPolicy(self, "PivotRolePolicy1",
                                 managed_policy_name=f"{env_resource_prefix}-pivotrole-policy-1",
                                 statements=[
                                     # Redshift
                                     iam.PolicyStatement(
                                         sid="Redshift", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "redshift:DeleteTags",
                                             "redshift:ModifyClusterIamRoles",
                                             "redshift:DescribeClusterSecurityGroups",
                                             "redshift:DescribeClusterSubnetGroups",
                                             "redshift:pauseCluster",
                                             "redshift:resumeCluster"
                                         ],
                                         resources=["*"],
                                         conditions={"StringEquals": {"aws:ResourceTag/dataall": "true"}}
                                     ),
                                     iam.PolicyStatement(
                                         sid="RedshiftRead", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "redshift:DescribeClusters",
                                             "redshift:CreateTags",
                                             "redshift:DescribeClusterSubnetGroups"
                                         ],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="RedshiftCreds", effect=iam.Effect.ALLOW,
                                         actions=["redshift:GetClusterCredentials"],
                                         resources=[
                                             f"arn:aws:redshift:*:{self.account}:dbgroup:*/*",
                                             f"arn:aws:redshift:*:{self.account}:dbname:*/*",
                                             f"arn:aws:redshift:*:{self.account}:dbuser:*/*"
                                         ]
                                     ),
                                     iam.PolicyStatement(
                                         sid="AllowRedshiftSubnet", effect=iam.Effect.ALLOW,
                                         actions=["redshift:CreateClusterSubnetGroup"],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="AllowRedshiftDataApi", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "redshift-data:ListTables",
                                             "redshift-data:GetStatementResult",
                                             "redshift-data:CancelStatement",
                                             "redshift-data:ListSchemas",
                                             "redshift-data:ExecuteStatement",
                                             "redshift-data:ListStatements",
                                             "redshift-data:ListDatabases",
                                             "redshift-data:DescribeStatement"
                                         ],
                                         resources=["*"]
                                     ),
                                     # EC2
                                     iam.PolicyStatement(
                                         sid="EC2SG", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "ec2:CreateSecurityGroup",
                                             "ec2:CreateNetworkInterface",
                                             "ec2:Describe*"
                                         ],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="TagsforENI", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "ec2:CreateTags",
                                             "ec2:DeleteTags"
                                         ],
                                         resources=[f"arn:aws:ec2:*:{self.account}:network-interface/*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="DeleteENI", effect=iam.Effect.ALLOW,
                                         actions=["ec2:DeleteNetworkInterface"],
                                         resources=["*"],
                                         conditions={"StringEquals": {"aws:ResourceTag/dataall": "True"}}
                                     ),
                                     # SageMaker
                                     iam.PolicyStatement(
                                         sid="SageMakerNotebookActions", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "sagemaker:ListTags",
                                             "sagemaker:DescribeUserProfile",
                                             "sagemaker:DeleteNotebookInstance",
                                             "sagemaker:StopNotebookInstance",
                                             "sagemaker:CreatePresignedNotebookInstanceUrl",
                                             "sagemaker:DescribeNotebookInstance",
                                             "sagemaker:StartNotebookInstance",
                                             "sagemaker:AddTags",
                                             "sagemaker:DescribeDomain",
                                             "sagemaker:CreatePresignedDomainUrl"
                                         ],
                                         resources=[
                                             f"arn:aws:sagemaker:*:{self.account}:notebook-instance/{env_resource_prefix}*",
                                             f"arn:aws:sagemaker:*:{self.account}:domain/*",
                                             f"arn:aws:sagemaker:*:{self.account}:user-profile/*/*"
                                         ]
                                     ),
                                     iam.PolicyStatement(
                                         sid="SageMakerNotebookInstances", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "sagemaker:ListNotebookInstances",
                                             "sagemaker:ListDomains",
                                             "sagemaker:ListApps",
                                             "sagemaker:DeleteApp"
                                         ],
                                         resources=["*"]
                                     ),
                                     # RAM
                                     iam.PolicyStatement(
                                         sid="RamTag", effect=iam.Effect.ALLOW,
                                         actions=["ram:TagResource"],
                                         resources=["*"],
                                         conditions={"ForAllValues:StringLike": {
                                             "ram:ResourceShareName": ["LakeFormation*"]}}
                                     ),
                                     iam.PolicyStatement(
                                         sid="RamCreateResource", effect=iam.Effect.ALLOW,
                                         actions=["ram:CreateResourceShare"],
                                         resources=["*"],
                                         conditions={"ForAllValues:StringEquals": {"ram:RequestedResourceType": [
                                             "glue:Table",
                                             "glue:Database",
                                             "glue:Catalog"
                                         ]}}
                                     ),
                                     iam.PolicyStatement(
                                         sid="RamUpdateResource", effect=iam.Effect.ALLOW,
                                         actions=["ram:UpdateResourceShare"],
                                         resources=[f"arn:aws:ram:*:{self.account}:resource-share/*"],
                                         conditions={
                                             "StringEquals": {"aws:ResourceTag/dataall": "true"},
                                             "ForAllValues:StringLike": {
                                                 "ram:ResourceShareName": ["LakeFormation*"]}
                                         }
                                     ),
                                     iam.PolicyStatement(
                                         sid="RamAssociateResource", effect=iam.Effect.ALLOW,
                                         actions=["ram:AssociateResourceShare"],
                                         resources=[f"arn:aws:ram:*:{self.account}:resource-share/*"],
                                         conditions={"ForAllValues:StringLike": {
                                                 "ram:ResourceShareName": ["LakeFormation*"]}
                                         }
                                     ),
                                     iam.PolicyStatement(
                                         sid="RamDeleteResource", effect=iam.Effect.ALLOW,
                                         actions=["ram:DeleteResourceShare"],
                                         resources=[f"arn:aws:ram:*:{self.account}:resource-share/*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="RamInvitations", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "ram:AcceptResourceShareInvitation",
                                             "ram:RejectResourceShareInvitation",
                                             "ec2:DescribeAvailabilityZones",
                                             "ram:EnableSharingWithAwsOrganization"
                                         ],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="RamRead", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "glue:PutResourcePolicy",
                                             "ram:Get*",
                                             "ram:List*"
                                         ],
                                         resources=["*"]
                                     ),
                                     # Security Groups
                                     iam.PolicyStatement(
                                         sid="SGCreateTag", effect=iam.Effect.ALLOW,
                                         actions=["ec2:CreateTags"],
                                         resources=[f"arn:aws:ec2:*:{self.account}:security-group/*"],
                                         conditions={"StringEquals": {"aws:RequestTag/dataall": "true"}}
                                     ),
                                     iam.PolicyStatement(
                                         sid="SGandRedshift", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "ec2:DeleteTags",
                                             "ec2:DeleteSecurityGroup",
                                             "redshift:DeleteClusterSubnetGroup"
                                         ],
                                         resources=["*"],
                                         conditions={"ForAnyValue:StringEqualsIfExists": {
                                             "aws:ResourceTag/dataall": "true"}}
                                     ),
                                     # Redshift
                                     iam.PolicyStatement(
                                         sid="RedshiftDataApi", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "redshift-data:ListTables",
                                             "redshift-data:GetStatementResult",
                                             "redshift-data:CancelStatement",
                                             "redshift-data:ListSchemas",
                                             "redshift-data:ExecuteStatement",
                                             "redshift-data:ListStatements",
                                             "redshift-data:ListDatabases",
                                             "redshift-data:DescribeStatement"
                                         ],
                                         resources=["*"],
                                         conditions={"StringEqualsIfExists": {"aws:ResourceTag/dataall": "true"}}
                                     ),
                                     # Dev Tools
                                     iam.PolicyStatement(
                                         sid="DevTools0", effect=iam.Effect.ALLOW,
                                         actions=["cloudformation:ValidateTemplate"],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="DevTools1", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "secretsmanager:CreateSecret",
                                             "secretsmanager:DeleteSecret",
                                             "secretsmanager:TagResource",
                                             "codebuild:DeleteProject"
                                         ],
                                         resources=["*"],
                                         conditions={"StringEquals": {"aws:ResourceTag/dataall": "true"}}
                                     ),
                                     iam.PolicyStatement(
                                         sid="DevTools2", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "codebuild:CreateProject",
                                             "ecr:CreateRepository",
                                             "ssm:PutParameter",
                                             "ssm:AddTagsToResource"
                                         ],
                                         resources=["*"],
                                         conditions={"StringEquals": {"aws:RequestTag/dataall": "true"}}
                                     ),
                                     iam.PolicyStatement(
                                         sid="CloudFormation", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "cloudformation:DescribeStacks",
                                             "cloudformation:DescribeStackResources",
                                             "cloudformation:DescribeStackEvents",
                                             "cloudformation:DeleteStack",
                                             "cloudformation:CreateStack",
                                             "cloudformation:GetTemplate",
                                             "cloudformation:ListStackResources",
                                             "cloudformation:DescribeStackResource"
                                         ],
                                         resources=[
                                             f"arn:aws:cloudformation:*:{self.account}:stack/{env_resource_prefix}*/*",
                                             f"arn:aws:cloudformation:*:{self.account}:stack/CDKToolkit/*",
                                             f"arn:aws:cloudformation:*:{self.account}:stack/*/*"
                                         ]
                                     )
                                 ]
                                 )

    def _create_dataall_policy2(self, env_resource_prefix: str) -> iam.ManagedPolicy:
        """
        Creates the third managed IAM Policy required for the Pivot Role used by data.all

        :param str env_resource_prefix: Environment Resource Prefix provided by data.all
        :returns: Created IAM Policy
        :rtype: iam.ManagedPolicy
        """
        return iam.ManagedPolicy(self, "PivotRolePolicy2",
                                 managed_policy_name=f"{env_resource_prefix}-pivotrole-policy-2",
                                 statements=[
                                     # LakeFormation
                                     iam.PolicyStatement(
                                         sid="LakeFormation", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "lakeformation:AddLFTagsToResource",
                                             "lakeformation:RemoveLFTagsFromResource",
                                             "lakeformation:GetResourceLFTags",
                                             "lakeformation:ListLFTags",
                                             "lakeformation:CreateLFTag",
                                             "lakeformation:GetLFTag",
                                             "lakeformation:UpdateLFTag",
                                             "lakeformation:DeleteLFTag",
                                             "lakeformation:SearchTablesByLFTags",
                                             "lakeformation:SearchDatabasesByLFTags",
                                             "lakeformation:ListResources",
                                             "lakeformation:ListPermissions",
                                             "lakeformation:GrantPermissions",
                                             "lakeformation:BatchGrantPermissions",
                                             "lakeformation:RevokePermissions",
                                             "lakeformation:BatchRevokePermissions",
                                             "lakeformation:PutDataLakeSettings",
                                             "lakeformation:GetDataLakeSettings",
                                             "lakeformation:GetDataAccess",
                                             "lakeformation:GetWorkUnits",
                                             "lakeformation:StartQueryPlanning",
                                             "lakeformation:GetWorkUnitResults",
                                             "lakeformation:GetQueryState",
                                             "lakeformation:GetQueryStatistics",
                                             "lakeformation:StartTransaction",
                                             "lakeformation:CommitTransaction",
                                             "lakeformation:CancelTransaction",
                                             "lakeformation:ExtendTransaction",
                                             "lakeformation:DescribeTransaction",
                                             "lakeformation:ListTransactions",
                                             "lakeformation:GetTableObjects",
                                             "lakeformation:UpdateTableObjects",
                                             "lakeformation:DeleteObjectsOnCancel",
                                             "lakeformation:DescribeResource"
                                         ],
                                         resources=["*"]
                                     ),
                                     # Compute
                                     iam.PolicyStatement(
                                         sid="Compute", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "lambda:CreateFunction",
                                             "lambda:AddPermission",
                                             "lambda:InvokeFunction",
                                             "lambda:RemovePermission",
                                             "lambda:GetFunction",
                                             "lambda:GetFunctionConfiguration",
                                             "lambda:DeleteFunction",
                                             "ecr:CreateRepository",
                                             "ecr:SetRepositoryPolicy",
                                             "ecr:DeleteRepository",
                                             "ecr:DescribeImages",
                                             "ecr:BatchDeleteImage",
                                             "codepipeline:GetPipelineState",
                                             "codepipeline:DeletePipeline",
                                             "codepipeline:GetPipeline",
                                             "codepipeline:CreatePipeline",
                                             "codepipeline:TagResource",
                                             "codepipeline:UntagResource"
                                         ],
                                         resources=[
                                             f"arn:aws:lambda:*:{self.account}:function:{env_resource_prefix}*",
                                             f"arn:aws:s3:::{env_resource_prefix}*",
                                             f"arn:aws:codepipeline:*:{self.account}:{env_resource_prefix}*",
                                             f"arn:aws:ecr:*:{self.account}:repository/{env_resource_prefix}*"
                                         ]
                                     ),
                                     # Databrew
                                     iam.PolicyStatement(
                                         sid="DatabrewList", effect=iam.Effect.ALLOW,
                                         actions=["databrew:List*"],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="DatabrewPermissions", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "databrew:BatchDeleteRecipeVersion",
                                             "databrew:Delete*",
                                             "databrew:Describe*",
                                             "databrew:PublishRecipe",
                                             "databrew:SendProjectSessionAction",
                                             "databrew:Start*",
                                             "databrew:Stop*",
                                             "databrew:TagResource",
                                             "databrew:UntagResource",
                                             "databrew:Update*"
                                         ],
                                         resources=[f"arn:aws:databrew:*:{self.account}:*/{env_resource_prefix}*"]
                                     ),
                                     # QuickSight
                                     iam.PolicyStatement(
                                         sid="QuickSight", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "quicksight:CreateGroup",
                                             "quicksight:DescribeGroup",
                                             "quicksight:ListDashboards",
                                             "quicksight:DescribeDataSource",
                                             "quicksight:DescribeDashboard",
                                             "quicksight:DescribeUser",
                                             "quicksight:SearchDashboards",
                                             "quicksight:GetDashboardEmbedUrl",
                                             "quicksight:GenerateEmbedUrlForAnonymousUser",
                                             "quicksight:UpdateUser",
                                             "quicksight:ListUserGroups",
                                             "quicksight:RegisterUser",
                                             "quicksight:DescribeDashboardPermissions",
                                             "quicksight:GetAuthCode",
                                             "quicksight:CreateGroupMembership",
                                             "quicksight:DescribeAccountSubscription"
                                         ],
                                         resources=[
                                             f"arn:aws:quicksight:*:{self.account}:group/default/dataall",
                                             f"arn:aws:quicksight:*:{self.account}:user/default/*",
                                             f"arn:aws:quicksight:*:{self.account}:datasource/*",
                                             f"arn:aws:quicksight:*:{self.account}:user/*",
                                             f"arn:aws:quicksight:*:{self.account}:dashboard/*",
                                             f"arn:aws:quicksight:*:{self.account}:namespace/default",
                                             f"arn:aws:quicksight:*:{self.account}:account/*"
                                         ]
                                     ),
                                     iam.PolicyStatement(
                                         sid="QuickSightSession", effect=iam.Effect.ALLOW,
                                         actions=["quicksight:GetSessionEmbedUrl"],
                                         resources=["*"]
                                     )
                                 ]
                                 )

    def _create_dataall_policy3(self, env_resource_prefix: str, role_name: str) -> iam.ManagedPolicy:
        """
        Creates the fourth managed IAM Policy required for the Pivot Role used by data.all

        :param str env_resource_prefix: Environment Resource Prefix provided by data.all
        :param str role_name: IAM Role name
        :returns: Created IAM Policy
        :rtype: iam.ManagedPolicy
        """
        return iam.ManagedPolicy(self, "PivotRolePolicy3",
                                 managed_policy_name=f"{env_resource_prefix}-pivotrole-policy-3",
                                 statements=[
                                     # SSM Parameter Store
                                     iam.PolicyStatement(
                                         sid="ParameterStore", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "ssm:GetParameter"
                                         ],
                                         resources=[
                                             f"arn:aws:ssm:*:{self.account}:parameter/{env_resource_prefix}/*",
                                             f"arn:aws:ssm:*:{self.account}:parameter/dataall/*",
                                             f"arn:aws:ssm:*:{self.account}:parameter/ddk/*"
                                         ]
                                     ),
                                     # Secrets Manager
                                     iam.PolicyStatement(
                                         sid="SecretsManager", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "secretsmanager:DescribeSecret",
                                             "secretsmanager:GetSecretValue"
                                         ],
                                         resources=[
                                             f"arn:aws:secretsmanager:*:{self.account}:secret:{env_resource_prefix}*",
                                             f"arn:aws:secretsmanager:*:{self.account}:secret:dataall*"
                                         ]
                                     ),
                                     iam.PolicyStatement(
                                         sid="SecretsManagerList", effect=iam.Effect.ALLOW,
                                         actions=["secretsmanager:ListSecrets"],
                                         resources=["*"]
                                     ),
                                     # IAM
                                     iam.PolicyStatement(
                                         sid="IAMListGet", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "iam:ListRoles",
                                             "iam:Get*"
                                         ],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="IAMRolePolicy", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "iam:PutRolePolicy",
                                             "iam:DeleteRolePolicy"
                                         ],
                                         resources=["*"]
                                     ),
                                     iam.PolicyStatement(
                                         sid="IAMPassRole", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "iam:PassRole"
                                         ],
                                         resources=[
                                             f"arn:aws:iam::{self.account}:role/{env_resource_prefix}*",
                                             f"arn:aws:iam::{self.account}:role/{role_name}",
                                             f"arn:aws:iam::{self.account}:role/cdk-*"
                                         ],
                                     ),
                                     # STS
                                     iam.PolicyStatement(
                                         sid="STS", effect=iam.Effect.ALLOW,
                                         actions=["sts:AssumeRole"],
                                         resources=[
                                             f"arn:aws:iam::{self.account}:role/{env_resource_prefix}*",
                                             f"arn:aws:iam::{self.account}:role/ddk-*"
                                         ]
                                     ),
                                     # Step Functions
                                     iam.PolicyStatement(
                                         sid="StepFunctions", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "states:DescribeStateMachine",
                                             "states:ListExecutions",
                                             "states:StartExecution"
                                         ],
                                         resources=[
                                             f"arn:aws:states:*:{self.account}:stateMachine:{env_resource_prefix}*"]
                                     ),
                                     # CodeCommit
                                     iam.PolicyStatement(
                                         sid="CodeCommit", effect=iam.Effect.ALLOW,
                                         actions=[
                                             "codecommit:GetFile",
                                             "codecommit:ListBranches",
                                             "codecommit:GetFolder",
                                             "codecommit:GetCommit",
                                             "codecommit:GitPull",
                                             "codecommit:GetRepository",
                                             'codecommit:TagResource',
                                             "codecommit:UntagResource",
                                             "codecommit:CreateBranch",
                                             "codecommit:CreateCommit",
                                             "codecommit:CreateRepository",
                                             "codecommit:DeleteRepository",
                                             "codecommit:GitPush",
                                             "codecommit:PutFile",
                                             "codecommit:GetBranch",
                                         ],
                                         resources=[f"arn:aws:codecommit:*:{self.account}:{env_resource_prefix}*"]
                                     )
                                 ]
                                 )



        
        
        
