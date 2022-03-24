# **Security**

data.all enforces security best practices on AWS Resources that it creates, in terms
of encryption, access control and traceability.

## **1. Authentication**

Users in data.all are authenticated against AWS Cognito, which supports Saml2 and Oauth federation.
Cognito can be federated with a corporate Identity Provider, such
as Okta or Active Directory (including Azure AD 365). 


!!!abstract "data.all doesn't have a user store and does not create or manage groups."
    It relies only on information provided by IdP as username, email, groups
    etc...

![Screenshot](assets/auth.png#zoom#shadow){: style="width:80%"}


## **2. Frontend (Static Sites)**

### **Overview**

data.all solution comes with 3 different static sites that are served to
the users:

1.  data.all User Interface: React JS application that integrates with
    AWS Cognito for user authentication, which is also the main UI.

2.  data.all development guide: Static HTML documents generated from
    markdown files using Mkdocs library available to all users having
    access to the server hosting the documentation.

3.  data.all user guide: Static HTML documents generated from markdown
    files using Mkdocs library available to all users having access to
    the server hosting the documentation.

### **Hosting**

data.all static sites are hosted on Amazon ECS using docker containers:

![](assets/vpconly/image3.png#zoom#shadow)

### **Networking**

data.all static sites are deployed on an AWS internal application load
balancer (ALB) deployed on the VPC's private subnet. This ALB is
reachable only from Amazon VPCs and not from the internet.

### **Security**

#### **Third party libraries**

data.all static sites libraries are stored on AWS CodeArtifact which
ensures third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.

#### **Docker images**

data.all base image for static sites is an AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.

## **3. Backend**
### **Overview**

data.all backend main entry point is an AWS API Gateway that exposes
GraphQL operations and stores data to an Amazon Aurora Serverless DB and
Amazon ElasticSearch cluster.

![](assets/vpconly/image4.png#zoom#shadow)

### **GraphQL API Gateway**
#### **Networking**

API Gateway is private and not exposed to the internet, it's linked to
shared VPC endpoint provided by the Cloud Foundations. There is also a
resource policy denying any traffic with a source different than the VPC
endpoint.

#### **Security**

API Gateway is protected by AWS Web Application Firewall (WAF) against
malicious attacks.

### **Lambda Functions**

data.all relies on lambda functions for API Authorization, and business
logic.

#### **Networking**

All data.all lambda functions are running inside a VPC and private
subnets.

#### **Security**

#### **Third party libraries**

data.all Lambda functions are stored on AWS CodeArtifact which ensures
third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.

#### **Docker images**

data.all base image for Lambda functions is an AWS approved Amazon Linux
base image, and does not rely on Dockerhub. Docker images are built with
AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

### **ECS services**

data.all uses ECS tasks as microservices to do long running taks or
scheduled tasks.

#### **Networking**

All ECS tasks are running inside a VPC and private subnets.

#### **Security**

#### **Third party libraries**

data.all ECS backend service docker images are built with AWS
CodePipeline and stored on AWS CodeArtifact which ensures third party
libraries availability, encryption using AWS KMS and auditability
through AWS CloudTrail.

#### **Docker images**

data.all base image for ECS backend service is an AWS approved Amazon
Linux base image, and does not rely on Dockerhub. Docker images are
built with AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

### **Aurora Serverless Database**

data.all uses Aurora serverless database to store data.all model metadata like
datasets, environments, etc.

#### **Networking**

Aurora database is running inside a VPC and private subnets, and is
accessible only by data.all resources like Lambda functions and ECS tasks
through security groups inbound rules.

#### **Security**

Aurora database is encrypted with AWS KMS key with enabled rotation.

### **Amazon OpenSearch cluster**

data.all uses Amazon OpenSearch cluster to index datasets information
for optimal search experience on the catalog.

#### **Networking**

Amazon OpenSearch cluster is running inside a VPC and private
subnets, and is accessible only by data.all resources like Lambda
functions and ECS tasks through security groups inbound rules.

#### **Security**

Amazon OpenSearch cluster is encrypted with AWS KMS key with enabled
rotation.

### **Amazon SQS FIFO Queue**

data.all uses Amazon SQS FIFO queue as a messaging mechanism between
backend API Lambda functions and the short running AWS tasks Lambda
function.

#### **Networking**

Amazon SQS queue is running outside of the VPC.

#### **Security**

Amazon SQS queue is encrypted with AWS KMS key with enabled
rotation.

## **4. CI/CD Pipeline**

### **Overview**

data.all infrastructure is deployed using AWS CodePipeline. data.all CI/CD
was built with cross accounts deployments in mind using AWS CDK
pipelines.

![](assets/vpconly/image5.png#zoom#shadow)

### **Networking**

AWS CodeBuild projects are part of the CI/CD pipeline are running inside a
VPC and private subnets.

### **Security**

### **Third party libraries**

data.all dependencies are stored on AWS CodeArtifact which ensures third
party libraries availability, encryption using AWS KMS and auditability
through AWS CloudTrail.

The quality gate stage of the CI/CD pipeline scans third party libraries
for vulnerabilities using safety and bandit python libraries.

### **Docker images**

data.all base image for all components is AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.

### **Aurora serverless database**

Integration tests Aurora serverless database is encrypted with KMS and
has rotation enabled. Security groups of the database is allowing
Codebuild projects only to access the database.

## **5. data.all Environments**

### **Overview**

An environment on data.all is an AWS account that verifies two
conditions:

1.  data.allPivotRole IAM role is created on the AWS account and trusts data.all deployment account.
2.  AWS account is bootstrapped with CDK and is trusting data.all deployment account.

### **data.all Pivot Role ExternalId**

Each data.all environment must have an AWS IAM role 
**PivotRole** that trusts data.all deployment account, so that
it could assume that role and do AWS operations like list AWS Glue
database tables etc. It is named **dataallPivotRole** by default, but other names can be assigned.

The **dataall-PivotRole** is secured with an **externalId** that the
pivot role must be created with; otherwise the STS AssumeRole operation
will fail. This is a recommended pattern from AWS
see [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html) to
grant access to external AWS accounts.

The **externalId** is created with the data.all infrastructure and is
stored on AWS Secretsmanager encrypted with a KMS key. Only users with
access to data.all can see and use the externalId.

![](assets/vpconly/image6.png#zoom#shadow)

### **data.all Pivot Role Template**
It is included as part of the codebase and can be modified to restrict or customize access.

`````yaml
AWSTemplateFormatVersion: 2010-09-09
Description: IAM Role used by dataall platform to run AWS short running tasks
Parameters:
  AwsAccountId:
    Description: AWS AccountId of the dataall environment
    Type: String
  ExternalId:
    Description: ExternalId to secure dataall assume role
    Type: String
  PivotRoleName:
    Description: IAM role name
    Type: String
  EnvironmentResourcePrefix:
    Description: The resource prefix value of the dataall environment
    Type: String
Resources:
  PivotRole:
    Type: 'AWS::IAM::Role'
    Properties:
      RoleName: !Ref PivotRoleName
      Path: /
      MaxSessionDuration: 43200
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - glue.amazonaws.com
                - lakeformation.amazonaws.com
                - lambda.amazonaws.com
            Action:
              - 'sts:AssumeRole'
          - Effect: Allow
            Principal:
              AWS:
                - !Ref AwsAccountId
            Action:
              - 'sts:AssumeRole'
            Condition:
              StringEquals:
                'sts:ExternalId': !Ref ExternalId
  PivotRolePolicy0:
    Type: 'AWS::IAM::ManagedPolicy'
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: Athena
            Action:
              - 'athena:GetQuery*'
              - 'athena:StartQueryExecution'
              - 'athena:ListWorkGroups'
            Effect: Allow
            Resource: '*'
          - Sid: AthenaWorkgroups
            Action:
              - 'athena:GetWorkGroup'
              - 'athena:CreateWorkGroup'
              - 'athena:UpdateWorkGroup'
              - 'athena:DeleteWorkGroup'
              - 'athena:TagResource'
              - 'athena:UntagResource'
              - 'athena:ListTagsForResource'
            Effect: Allow
            Resource: !Sub 'arn:aws:athena:*:${AWS::AccountId}:workgroup/${EnvironmentResourcePrefix}*'
          - Sid: AwsGlueCrawlerBucket
            Effect: Allow
            Action: 's3:GetObject'
            Resource:
              - 'arn:aws:s3:::crawler-public*'
          - Sid: ManagedBuckets
            Action:
              - 's3:List*'
              - 's3:Delete*'
              - 's3:Get*'
              - 's3:Put*'
            Effect: Allow
            Resource:
              - !Sub 'arn:aws:s3:::${EnvironmentResourcePrefix}*'
          - Sid: ImportedBuckets
            Action:
              - 's3:List*'
              - 's3:GetBucket*'
              - 's3:GetLifecycleConfiguration'
              - 's3:GetObject'
              - 's3:PutBucketPolicy'
              - 's3:PutBucketTagging'
              - 's3:PutObject'
              - 's3:PutObjectAcl'
              - 's3:PutBucketOwnershipControls'
            Effect: Allow
            Resource:
              - 'arn:aws:s3:::*'
          - Sid: AWSLoggingBuckets
            Action:
              - 's3:PutBucketAcl'
              - 's3:PutBucketNotification'
            Effect: Allow
            Resource:
              - !Sub 'arn:aws:s3:::${EnvironmentResourcePrefix}-logging-*'
          - Sid: ReadBuckets
            Action:
              - 's3:ListAllMyBuckets'
              - 's3:GetBucketLocation'
              - 's3:PutBucketTagging'
            Effect: Allow
            Resource: '*'
          - Sid: CWMetrics
            Action:
              - 'cloudwatch:PutMetricData'
              - 'cloudwatch:GetMetricData'
              - 'cloudwatch:GetMetricStatistics'
            Effect: Allow
            Resource: '*'
          - Sid: Logs
            Effect: Allow
            Action:
              - 'logs:CreateLogGroup'
              - 'logs:CreateLogStream'
              - 'logs:PutLogEvents'
            Resource:
              - !Sub 'arn:aws:logs:*:${AWS::AccountId}:/aws-glue/*'
              - !Sub 'arn:aws:logs:*:${AWS::AccountId}:/aws-lambda/*'
              - !Sub 'arn:aws:logs:*:${AWS::AccountId}:/${EnvironmentResourcePrefix}*'
          - Sid: Logging
            Action:
              - 'logs:PutLogEvents'
            Effect: Allow
            Resource: '*'
          - Sid: CWEvents
            Action:
              - 'events:DeleteRule'
              - 'events:List*'
              - 'events:PutRule'
              - 'events:PutTargets'
              - 'events:RemoveTargets'
            Effect: Allow
            Resource: '*'
          - Sid: Glue
            Action:
              - 'glue:BatchCreatePartition'
              - 'glue:BatchDeletePartition'
              - 'glue:BatchDeleteTable'
              - 'glue:CreateCrawler'
              - 'glue:CreateDatabase'
              - 'glue:CreatePartition'
              - 'glue:CreateTable'
              - 'glue:DeleteCrawler'
              - 'glue:DeleteDatabase'
              - 'glue:DeleteJob'
              - 'glue:DeletePartition'
              - 'glue:DeleteTable'
              - 'glue:DeleteTrigger'
              - 'glue:BatchGet*'
              - 'glue:Get*'
              - 'glue:List*'
              - 'glue:StartCrawler'
              - 'glue:StartJobRun'
              - 'glue:StartTrigger'
              - 'glue:SearchTables'
              - 'glue:UpdateDatabase'
              - 'glue:UpdatePartition'
              - 'glue:UpdateTable'
              - 'glue:UpdateTrigger'
              - 'glue:UpdateJob'
              - 'glue:TagResource'
            Effect: Allow
            Resource: '*'
          - Sid: KMS
            Action:
              - 'kms:Decrypt'
              - 'kms:Encrypt'
              - 'kms:GenerateDataKey*'
              - 'kms:PutKeyPolicy'
              - 'kms:ReEncrypt*'
              - 'kms:TagResource'
              - 'kms:UntagResource'
            Effect: Allow
            Resource:
              - '*'
          - Sid: KMSAlias
            Action:
              - 'kms:DeleteAlias'
            Effect: Allow
            Resource:
              - !Sub 'arn:aws:kms:*:${AWS::AccountId}:alias/${EnvironmentResourcePrefix}*'
          - Sid: KMSCreate
            Action:
              - 'kms:List*'
              - 'kms:DescribeKey'
              - 'kms:CreateAlias'
              - 'kms:CreateKey'
            Effect: Allow
            Resource: '*'
          - Sid: Organizations
            Action: 'organizations:DescribeOrganization'
            Effect: Allow
            Resource: '*'
          - Sid: ResourcesGroupTags
            Action:
              - 'tag:*'
              - 'resource-groups:*'
            Effect: Allow
            Resource: '*'
          - Sid: SNSPublish
            Action:
              - 'sns:Publish'
              - 'sns:SetTopicAttributes'
              - 'sns:GetTopicAttributes'
              - 'sns:DeleteTopic'
              - 'sns:Subscribe'
              - 'sns:TagResource'
              - 'sns:UntagResource'
              - 'sns:CreateTopic'
            Effect: Allow
            Resource: !Sub 'arn:aws:sns:*:${AWS::AccountId}:${EnvironmentResourcePrefix}*'
          - Sid: SNSList
            Action:
              - 'sns:ListTopics'
            Effect: Allow
            Resource: '*'
          - Sid: SQSList
            Action:
              - 'sqs:ListQueues'
            Effect: Allow
            Resource: '*'
          - Sid: SQS
            Action:
              - 'sqs:ReceiveMessage'
              - 'sqs:SendMessage'
            Effect: Allow
            Resource: !Sub 'arn:aws:sqs:*:${AWS::AccountId}:${EnvironmentResourcePrefix}*'
      ManagedPolicyName: !Sub ${EnvironmentResourcePrefix}-pivotrole-policy-0
      Roles:
        - !Ref PivotRoleName
    DependsOn: PivotRole

  PivotRolePolicy1:
    Type: 'AWS::IAM::ManagedPolicy'
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: Redshift
            Effect: Allow
            Action:
              - 'redshift:DeleteTags'
              - 'redshift:ModifyClusterIamRoles'
              - 'redshift:DescribeClusterSecurityGroups'
              - 'redshift:DescribeClusterSubnetGroups'
              - 'redshift:pauseCluster'
              - 'redshift:resumeCluster'
            Resource: '*'
            Condition:
              StringEquals:
                'aws:ResourceTag/dataall': 'true'
          - Sid: RedshiftRead
            Effect: Allow
            Action:
              - 'redshift:DescribeClusters'
              - 'redshift:CreateTags'
              - 'redshift:DescribeClusterSubnetGroups'
            Resource: '*'
          - Sid: RedshiftCreds
            Effect: Allow
            Action:
              - 'redshift:GetClusterCredentials'
            Resource:
              - !Sub 'arn:aws:redshift:*:${AWS::AccountId}:dbgroup:*/*'
              - !Sub 'arn:aws:redshift:*:${AWS::AccountId}:dbname:*/*'
              - !Sub 'arn:aws:redshift:*:${AWS::AccountId}:dbuser:*/*'
          - Sid: AllowRedshiftSubnet
            Effect: Allow
            Action:
              - 'redshift:CreateClusterSubnetGroup'
            Resource: '*'
          - Sid: AllowRedshiftDataApi
            Effect: Allow
            Action:
              - 'redshift-data:ListTables'
              - 'redshift-data:GetStatementResult'
              - 'redshift-data:CancelStatement'
              - 'redshift-data:ListSchemas'
              - 'redshift-data:ExecuteStatement'
              - 'redshift-data:ListStatements'
              - 'redshift-data:ListDatabases'
              - 'redshift-data:DescribeStatement'
            Resource: '*'
          - Sid: EC2SG
            Effect: Allow
            Action:
              - 'ec2:CreateSecurityGroup'
              - 'ec2:CreateNetworkInterface'
              - 'ec2:Describe*'
            Resource: '*'
          - Sid: TagsforENI
            Effect: Allow
            Action:
              - 'ec2:DeleteTags'
              - 'ec2:CreateTags'
            Resource: !Sub 'arn:aws:ec2:*:${AWS::AccountId}:network-interface/*'
          - Sid: DeleteENI
            Effect: Allow
            Action:
              - 'ec2:DeleteNetworkInterface'
            Resource: '*'
            Condition:
              StringEquals:
                'aws:ResourceTag/dataall': 'True'
          - Sid: SageMakerNotebookActions
            Effect: Allow
            Action:
              - 'sagemaker:ListTags'
              - 'sagemaker:DeleteNotebookInstance'
              - 'sagemaker:StopNotebookInstance'
              - 'sagemaker:CreatePresignedNotebookInstanceUrl'
              - 'sagemaker:DescribeNotebookInstance'
              - 'sagemaker:StartNotebookInstance'
              - 'sagemaker:AddTags'
              - 'sagemaker:DescribeDomain'
            Resource:
              - !Sub 'arn:aws:sagemaker:*:${AWS::AccountId}:notebook-instance/${EnvironmentResourcePrefix}*'
              - !Sub 'arn:aws:sagemaker:*:${AWS::AccountId}:domain/*'
          - Sid: SagemakerNotebookInstances
            Effect: Allow
            Action:
             - 'sagemaker:ListNotebookInstances'
             - 'sagemaker:ListDomains'
            Resource: '*'
          - Effect: Allow
            Action:
              - 'ram:TagResource'
            Resource: '*'
            Condition:
              'ForAllValues:StringLike':
                'ram:ResourceShareName':
                  - LakeFormation*
          - Effect: Allow
            Action:
              - 'ram:CreateResourceShare'
            Resource: '*'
            Condition:
              'ForAllValues:StringEquals':
                'ram:RequestedResourceType':
                  - 'glue:Table'
                  - 'glue:Database'
                  - 'glue:Catalog'
          - Effect: Allow
            Action:
              - 'ram:UpdateResourceShare'
            Resource: !Sub 'arn:aws:ram:*:${AWS::AccountId}:resource-share/*'
            Condition:
              StringEquals:
                'aws:ResourceTag/dataall': 'true'
              'ForAllValues:StringLike':
                'ram:ResourceShareName':
                  - LakeFormation*
          - Effect: Allow
            Action:
              - 'ram:DeleteResourceShare'
            Resource: !Sub 'arn:aws:ram:*:${AWS::AccountId}:resource-share/*'
            Condition:
              StringEqualsIfExists:
                'aws:ResourceTag/dataall': 'true'
          - Sid: RamInvitations
            Effect: Allow
            Action:
              - "ram:AcceptResourceShareInvitation"
              - "ram:RejectResourceShareInvitation"
              - "ec2:DescribeAvailabilityZones"
              - "ram:EnableSharingWithAwsOrganization"
            Resource: '*'
          - Effect: Allow
            Action:
              - 'glue:PutResourcePolicy'
              - 'ram:Get*'
              - 'ram:List*'
            Resource: '*'
          - Sid: SGCreateTag
            Effect: Allow
            Action:
              - 'ec2:CreateTags'
            Resource:
              - !Sub 'arn:aws:ec2:*:${AWS::AccountId}:security-group/*'
            Condition:
              StringEquals:
                'aws:RequestTag/dataall': 'true'
          - Sid: SGandRedshift
            Effect: Allow
            Action:
              - 'ec2:DeleteTags'
              - 'ec2:DeleteSecurityGroup'
              - 'redshift:DeleteClusterSubnetGroup'
            Resource:
              - '*'
            Condition:
              'ForAnyValue:StringEqualsIfExists':
                'aws:ResourceTag/dataall': 'true'
          - Sid: RedshiftDataApi
            Effect: Allow
            Action:
              - 'redshift-data:ListTables'
              - 'redshift-data:GetStatementResult'
              - 'redshift-data:CancelStatement'
              - 'redshift-data:ListSchemas'
              - 'redshift-data:ExecuteStatement'
              - 'redshift-data:ListStatements'
              - 'redshift-data:ListDatabases'
              - 'redshift-data:DescribeStatement'
            Resource: '*'
            Condition:
              StringEqualsIfExists:
                'aws:ResourceTag/dataall': 'true'
          - Sid: DevTools0
            Effect: Allow
            Action: 'cloudformation:ValidateTemplate'
            Resource: '*'
          - Sid: DevTools1
            Effect: Allow
            Action:
              - 'secretsmanager:CreateSecret'
              - 'secretsmanager:DeleteSecret'
              - 'secretsmanager:TagResource'
              - 'codebuild:DeleteProject'
            Resource: '*'
            Condition:
              StringEquals:
                'aws:ResourceTag/dataall': 'true'
          - Sid: DevTools2
            Effect: Allow
            Action:
              - 'codebuild:CreateProject'
              - 'ecr:CreateRepository'
              - 'ssm:PutParameter'
              - 'ssm:AddTagsToResource'
            Resource: '*'
            Condition:
              StringEquals:
                'aws:RequestTag/dataall': 'true'
          - Sid: CloudFormation
            Effect: Allow
            Action:
              - 'cloudformation:DescribeStacks'
              - 'cloudformation:DescribeStackResources'
              - 'cloudformation:DescribeStackEvents'
              - 'cloudformation:DeleteStack'
              - 'cloudformation:CreateStack'
              - 'cloudformation:GetTemplate'
            Resource: !Sub 'arn:aws:cloudformation:*:${AWS::AccountId}:stack/${EnvironmentResourcePrefix}*/*'
      ManagedPolicyName: !Sub ${EnvironmentResourcePrefix}-pivotrole-policy-1
      Roles:
        - !Ref PivotRoleName
    DependsOn: PivotRole

  PivotRolepolicy2:
    Type: 'AWS::IAM::ManagedPolicy'
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: LakeFormation
            Effect: Allow
            Action:
              - "lakeformation:AddLFTagsToResource"
              - "lakeformation:RemoveLFTagsFromResource"
              - "lakeformation:GetResourceLFTags"
              - "lakeformation:ListLFTags"
              - "lakeformation:CreateLFTag"
              - "lakeformation:GetLFTag"
              - "lakeformation:UpdateLFTag"
              - "lakeformation:DeleteLFTag"
              - "lakeformation:SearchTablesByLFTags"
              - "lakeformation:SearchDatabasesByLFTags"
              - 'lakeformation:ListResources'
              - 'lakeformation:ListPermissions'
              - 'lakeformation:GrantPermissions'
              - 'lakeformation:BatchGrantPermissions'
              - 'lakeformation:RevokePermissions'
              - 'lakeformation:BatchRevokePermissions'
              - 'lakeformation:PutDataLakeSettings'
              - 'lakeformation:GetDataLakeSettings'
              - 'lakeformation:GetDataAccess'
              - 'lakeformation:SearchTablesByLFTags'
              - 'lakeformation:SearchDatabasesByLFTags'
              - 'lakeformation:GetWorkUnits'
              - 'lakeformation:StartQueryPlanning'
              - 'lakeformation:GetWorkUnitResults'
              - 'lakeformation:GetQueryState'
              - 'lakeformation:GetQueryStatistics'
              - 'lakeformation:StartTransaction'
              - 'lakeformation:CommitTransaction'
              - 'lakeformation:CancelTransaction'
              - 'lakeformation:ExtendTransaction'
              - 'lakeformation:DescribeTransaction'
              - 'lakeformation:ListTransactions'
              - 'lakeformation:GetTableObjects'
              - 'lakeformation:UpdateTableObjects'
              - 'lakeformation:DeleteObjectsOnCancel'
            Resource: '*'
          - Sid: Compute
            Effect: Allow
            Action:
              - 'lambda:CreateFunction'
              - 'lambda:AddPermission'
              - 'lambda:InvokeFunction'
              - 'lambda:RemovePermission'
              - 'lambda:GetFunction'
              - 'lambda:GetFunctionConfiguration'
              - 'lambda:DeleteFunction'
              - 'ecr:CreateRepository'
              - 'ecr:SetRepositoryPolicy'
              - 'ecr:DeleteRepository'
              - 'ecr:DescribeImages'
              - 'ecr:BatchDeleteImage'
              - 'codepipeline:GetPipelineState'
              - 'codepipeline:DeletePipeline'
              - 'codepipeline:GetPipeline'
              - 'codepipeline:CreatePipeline'
              - 'codepipeline:TagResource'
              - 'codepipeline:UntagResource'
            Resource:
              - !Sub 'arn:aws:lambda:*:${AWS::AccountId}:function:${EnvironmentResourcePrefix}*'
              - !Sub 'arn:aws:s3:::${EnvironmentResourcePrefix}*'
              - !Sub 'arn:aws:codepipeline:*:${AWS::AccountId}:${EnvironmentResourcePrefix}*'
              - !Sub 'arn:aws:ecr:*:${AWS::AccountId}:repository/${EnvironmentResourcePrefix}*'
          - Sid: DatabrewList
            Effect: Allow
            Action:
              - 'databrew:List*'
            Resource: '*'
          - Sid: DatabrewPermissions
            Effect: Allow
            Action:
              - 'databrew:BatchDeleteRecipeVersion'
              - 'databrew:Delete*'
              - 'databrew:Describe*'
              - 'databrew:PublishRecipe'
              - 'databrew:SendProjectSessionAction'
              - 'databrew:Start*'
              - 'databrew:Stop*'
              - 'databrew:TagResource'
              - 'databrew:UntagResource'
              - 'databrew:Update*'
            Resource: !Sub 'arn:aws:databrew:*:${AWS::AccountId}:*/${EnvironmentResourcePrefix}*'
          - Sid: QuickSight
            Effect: Allow
            Action:
              - "quicksight:CreateGroup"
              - "quicksight:DescribeGroup"
              - "quicksight:ListDashboards"
              - "quicksight:DescribeDataSource"
              - "quicksight:DescribeDashboard"
              - "quicksight:DescribeUser"
              - "quicksight:SearchDashboards"
              - "quicksight:GetDashboardEmbedUrl"
              - "quicksight:GenerateEmbedUrlForAnonymousUser"
              - "quicksight:UpdateUser"
              - "quicksight:ListUserGroups"
              - "quicksight:RegisterUser"
              - "quicksight:DescribeDashboardPermissions"
              - "quicksight:GetAuthCode"
              - "quicksight:CreateGroupMembership"
            Resource:
            - !Sub "arn:aws:quicksight:*:${AWS::AccountId}:group/default/dataall"
            - !Sub "arn:aws:quicksight:*:${AWS::AccountId}:user/default/*"
            - !Sub "arn:aws:quicksight:*:${AWS::AccountId}:datasource/*"
            - !Sub "arn:aws:quicksight:*:${AWS::AccountId}:user/*"
            - !Sub "arn:aws:quicksight:*:${AWS::AccountId}:dashboard/*"
            - !Sub "arn:aws:quicksight:*:${AWS::AccountId}:namespace/default"
          - Sid: QuickSightSession
            Effect: Allow
            Action:
              - 'quicksight:GetSessionEmbedUrl'
            Resource: '*'
      ManagedPolicyName: !Sub ${EnvironmentResourcePrefix}-pivotrole-policy-2
      Roles:
        - !Ref PivotRoleName
    DependsOn: PivotRole

  PivotRolepolicy3:
    Type: 'AWS::IAM::ManagedPolicy'
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: Secretsmanager
            Effect: Allow
            Action:
              - "secretsmanager:DescribeSecret"
              - "secretsmanager:GetSecretValue"
            Resource: !Sub 'arn:aws:secretsmanager:*:${AWS::AccountId}:secret:${EnvironmentResourcePrefix}*'
          - Sid: SecretsmanagerList
            Effect: Allow
            Action:
              - "secretsmanager:ListSecrets"
            Resource: '*'
          - Sid: IAMList
            Action:
              - 'iam:ListRoles'
            Effect: Allow
            Resource: '*'
          - Sid: IAMPassRole
            Action:
              - 'iam:Get*'
              - 'iam:PassRole'
            Effect: Allow
            Resource:
              - !Sub 'arn:aws:iam::${AWS::AccountId}:role/${EnvironmentResourcePrefix}*'
              - !Sub 'arn:aws:iam::${AWS::AccountId}:role/${PivotRoleName}'
              - !Sub 'arn:aws:iam::${AWS::AccountId}:role/cdk-*'
          - Sid: STS
            Action:
              - 'sts:AssumeRole'
            Effect: Allow
            Resource:
              - !Sub 'arn:aws:iam::${AWS::AccountId}:role/${EnvironmentResourcePrefix}*'
          - Sid: StepFunctions
            Action:
              - 'states:DescribeStateMachine'
              - 'states:ListExecutions'
              - 'states:StartExecution'
            Effect: Allow
            Resource:
              - !Sub 'arn:aws:states:*:${AWS::AccountId}:stateMachine:${EnvironmentResourcePrefix}*'
      ManagedPolicyName: !Sub ${EnvironmentResourcePrefix}-pivotrole-policy-3
      Roles:
        - !Ref PivotRoleName
    DependsOn: PivotRole
Outputs:
  PivotRoleOutput:
    Description: Platform Pivot Role
    Value: PivotRole
    Export:
      Name: !Sub '${AWS::StackName}-PivotRole'

`````

## **6. data.all Resources**

### **Overview**

data.all resources are the objects created by the users through data.all
UI or API like datasets, notebooks, dashboards... We will discuss below
the security of the most critical data.all resources.

### **Datasets**

data.all stack deploys the following AWS resources:

![](assets/vpconly/image7.png#zoom#shadow)

| AWS Service | Resource          | Description 
|-------------|-------------------|-------------
| S3          | Bucket            | Amazon S3 Bucket where the dataset data is stored.        
| S3          | Bucket Policy     | data.all managed S3 Bucket Policy attached to the dataset bucket.        
| KMS         | Key/Alias         | Encryption key used to encrypt all data in the S3 Bucket.        
| IAM         | Role              | IAM role with R/W permissions on the dataset S3 bucket for firect access from data.all UI
| Glue        | Database          | AWS Glue database for the dataset.        
| Glue        | Tables            | AWS Glue table for each data.all table created.         
| Glue        | Job               | AWS Glue job profiling the dataset tables.       
| Glue        | Job               | AWS Glue jfor validating data quality rules on dataset tables.         
| S3          | Prefix            | Amazon S3 Bucket prefix for each data.all folder created.    


#### **Security**

Following security best practices, the following are configured automatically for each dataset:

- Encryption: Datasets are protected by AWS Managed KMS Keys, one key is generated for each Dataset.

- Traceability: All access to data is logged through AWS CloudTrail logs

- Data Access/Governance: All SQL queries from EMR, Redshift, Glue Jobs, Athena are automatically secured through Lake Formation

!!! abstract "Datasets are owned by data.all teams"
    Data access is secured through AWS Lake Formation and S3 Bucket Policies on the Glue database and tables and on the 
    dataset S3 Bucket correspondingly. If no sharing has taken place, only members of the Dataset owner team can access the S3 data
    and the Glue database and tables.

#### **Networking**

-   Glue jobs related to the dataset are by default running outside the VPC.

#### **Data sharing**

All data sharing is READ ONLY. When a dataset owner decides to share a
table, or a prefix with another Team, this will automatically update the
stack (infrastructure as code) of the dataset.

For structured data (tables):

-   The underlying Lake Formation tables will have an additional READ ONLY Grant, allowing the remote account to Select and List the data for the shared table

For unstructured data (folders):

-   The underlying S3 Bucket will be updated with an additional S3 Bucket Policy granting read only access to the remote account and team on the underlying S3 Prefix


#### **Extensibility**

Any security requirement can be fully automated through adding resources
to the stacks that define the dataset resources. This provides security
team with simple ways to add any security mechanism at the scale of the
data lake, as opposed to applying security on a project basics.

### **Warehouses**

Warehouse are Amazon Redshift Clusters created or imported by data.all
that allows data teams to implement secure, automated, data warehousing
including loading data from S3 through Spectrum

A warehouse in data.all is mapped to

  |Service|           Resource|   Description|
  |-----------------| ---------- |----------------------------------------------|
  |Redshift |         Cluster  |  Amazon Redshift cluster for data warehousing|
  |KMS|               Key |       Key encryption used by the Redshift cluster|
  |Secrets Manager|   Secret|     Stores Redshift cluster user credentials|

All resources are created automatically on an AWS Account/Region

#### **Security**

Following security means are configured automatically for each Redshift
cluster:

- Encryption: Amazon Redshift Cluster is encrypted with KMS.

- Traceability: All access to data is logged through AWS CloudTrail
    logs
- 
#### **Networking**
Redshift cluster is deployed only within a private subnet

### **Notebooks**

Notebooks in data.all are a concept that allows Data Scientists to build
machine learning models using Amazon Sagemaker Studio:


A notebook in data.all is mapped to

  |Service|     Resource|   Description|
  |----------- |---------- |-------------------------------|
  |SageMaker|   Instance|   SageMaker Studio user profile|

All resources are created automatically on an AWS Account/Region

#### **Security**

Following security means are configured automatically for each dataset:

-   Traceability: All access to data is logged through AWS CloudTrail
    logs

#### **Networking**

Sagemaker studio is running on the VPC and subnets provided by the user.

## **7. Application Security Model**

data.all permission model is based on group membership inherited from the
corporate IdP.

Each object in data.all will have

-   A **Creator** with full permissions on the object

-   A **Team** with full permissions on the object, the group is being
    federated with the Corporate IdP

### **Organizations**

Organizations are created by a team, and other teams (IdP groups) can be
invited on an organization to link their AWS accounts as data.all
environments.

Only the users belonging to the administrator's team and the invited
teams are allowed to see the organization.

### **Environments**

An environment is created by a user and associated with a Team. The team
members are administrators of the environment and they can invite other
teams.

Administrators of the environment can invite other IdP groups to
collaborate on the same environment. Administrators are able to grant
fine grained permissions which will create an IAM role with the same
permissions to access the AWS account.

Only the users belonging to the administrator's team and the invited
teams are allowed to access the underlying AWS account.

### **Datasets**

A dataset had one creator with technical permissions on the Dataset
metadata and underlying access to the data in AWS.

One technical admin team with same permissions as the dataset creator

Each Dataset must have a team of stewards (IdP group), granting or
denying access to the dataset items (tables/folders).

Finally, Dataset items can be shared with other environments and teams,
i.e. an another account and an IAM role, federated through corporate
IdP.

when a Table is shared, its shared across AWS account using AWS Lake
Formation cross account table sharing, allowing READ ONLY Access to the
shared table

when a folder is shared, the Bucket Policy of the Dataset is allowing
READ ONLY to the other account, in READ ONLY mode

### **Pipelines**

A Pipeline has one creator with technical permissions on the Pipeline
and underlying access to the data in AWS.

one technical admin team with same permissions as the Pipeline creator
that can run the Pipeline from the User Interface or API.

### **Dashboards**

A Dashboard has one creator with technical permissions on the Dashboard
and underlying access to the data in AWS.

one technical admin team with same permissions as the Dashboard Creator.
