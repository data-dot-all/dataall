---
layout: default
homePage: false
title: Architecture
permalink: /architecture/
---
# **Architecture**

1. [End-to-end architecture](#end)
2. [CICD in tooling account](#tooling)
3. [Infrastructure in deployment account(s)](#infrastructure)
   1. [Frontend Components](#frontend)
   2. [Backend Components](#backend)
4. [Linked Environments](#environment)

## End-to-end architecture <a name="end"></a>

![archi](img/architecture_complete.drawio.png#zoom#shadow)

## CICD in tooling account <a name="tooling"></a>

data.all infrastructure (in the deployment account(s)) is deployed from the tooling account using AWS CodePipeline.
Cloud resources in 
data.all are defined using the [AWS Cloud Development Kit](https://aws.amazon.com/cdk/) (AWS CDK).
data.all CI/CD was built with cross accounts deployments in mind using AWS CDK pipelines. 


![archi](img/architecture_tooling.drawio.png#zoom#shadow)


- As appears in the diagram, AWS CodeBuild projects which are part of the CI/CD pipeline are running inside a
VPC and private subnets. 


- data.all dependencies are stored on AWS CodeArtifact which ensures third
party libraries availability, encryption using AWS KMS and auditability
through AWS CloudTrail.

- The quality gate stage of the CI/CD pipeline scans third party libraries
for vulnerabilities using safety and bandit python libraries.

- Docker images: data.all base image for all components is AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.

- For the integration test stage we use an Aurora serverless database which is encrypted with KMS and
has rotation enabled. The database security groups allow access to the database to
Codebuild projects only.


## Infrastructure in deployment account(s) <a name="infrastructure"></a>
data.all infrastructure can be best understood when compared to 
a <span style="color:#2074d5">**classical 3-tier application**</span>,
implemented using mostly AWS serverless services.
As in classical web application, the three layers of data.all are:

1. Presentation layer (Amazon Cloudfront OR Amazon Application Load Balancer)
2. API layer:
    - Client (AWS API Gateway)
    - Server (AWS Lambda)
3. Persistence layer (Amazon Aurora serverless -- Postgres version)

The architecture <span style="color:#2074d5">**decouples**</span> data.all business logic (CRUD)
from the AWS logic and processing. To achieve this decoupling, the web application delegates any AWS related tasks to two components:

4. Long Running Background Tasks Processor (Amazon ECS Fargate)
5. Short Running Asynchronous Tasks Processor (AWS Lambda)

data.all infrastructure runs <span style="color:#2074d5">**90% on serverless**</span> services in a private VPC, 
the remaining 10% are for the OpenSearch cluster that is not serverless... yet!

![archi](img/architecture_infrastructure.drawio.png#zoom#shadow)

## Frontend Components <a name="frontend"></a>

To fit the requirements of enterprise grade customers, data.all architecture has two variants. Both 
architectures are part of data.all code base and can be configured with in the deployment with the 
`internet_facing` parameter of the configuration cdk.json file. Check the [Deploy to AWS](./deploy-aws/) section.

- Internet facing architecture
- VPC facing architecture

### Internet facing architecture
This architecture relies on AWS services living outside the VPC like S3 and CloudFront for data.all UI and 
user guide documentation hosting.
Backend APIs are public and can be reached from the internet. 
Internet facing services are protected with AWS Wep Application Firewall (WAF).


![](img/architecture_frontend_internet.drawio.png#zoom#shadow)

#### Users Authentication

Users in data.all are authenticated against AWS Cognito. 
In a typical step of data.all, Cognito is federated with a corporate Identity Provider, such
as Okta or Active Directory (including Azure AD 365). In this case Cognito acts as a simple proxy,
abstracting the different IdP providers protocols.

**Note**: data.all doesn't have a user store and does not create or manage groups.
It relies only on information provided by the IdP; such as username, email, groups, etc...


#### User Interface and User Guide
data.all UI and user guide website follow static websites pattern on AWS with CloudFront used as the 
Content Delivery Network (CDN).
CloudFront is protected  by Web Application Firewall (WAF) on top of S3 encrypted buckets hosting the sites assets.


- data.all UI frontend code is a <span style="color:#2074d5">**React application**</span>. Its code is bundled using React 
create-react-app utility, and saved to S3 as the Cloudfront distribution origin.

- data.all user guide consists of static HTML documents generated from markdown
files using Mkdocs library available to all users having access to
the server hosting the documentation.


### VPC facing architecture
In this architecture, data.all static sites are deployed on an AWS internal application load
balancer (ALB) deployed on the VPC's private subnet. 
This ALB is reachable only from Amazon VPCs and not from the internet. 
Also, APIs are private and accessible only through VPC endpoints.


Finally, data.all static sites are hosted on Amazon ECS using docker containers.



- Third party libraries: data.all static sites libraries are stored on AWS CodeArtifact which
ensures third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.

- Docker images: data.all base image for static sites is an AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.


![](img/architecture_frontend_vpc.drawio.png#zoom#shadow)


## Backend Components <a name="backend"></a>

![Screenshot](img/architecture_backend.drawio.png#zoom#shadow)

### VPC

data.all creates its own VPC in the account where it is set up, with usual configuration.
All compute is hosted in the **private subnets**, and communicates with AWS Services through a **NAT Gateway**.

All data.all Lambda functions and ECS tasks are running inside this VPC and in private
subnets. 



![Screenshot](img/architecture_vpc.drawio.png#zoom#shadow)

### Backend AWS API Gateway
data.all backend main entry point is an AWS API Gateway that exposes a
GraphQL API.

- API Gateway is private and not exposed to the internet, it's linked to a
shared VPC endpoint. 
- A resource policy on the API Gateway denys any traffic with a source different than the VPC
endpoint.
- API Gateway is protected by AWS Web Application Firewall (WAF) against
malicious attacks.

### Amazon Cognito Authorizer
As explained in the frontend section, Amazon Cognito is used for Authentication of users. 
In Amazon API Gateway we again use [Cognito for Authorization](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html). 
With an Amazon Cognito user pool, we control who can access our GraphQL API. 

### AWS Lambda - Backend or "API Handler" Lambda
This is the backend Lambda function that implements the business logic by processing the incoming GraphQL queries.
More information on GraphQL can be found in their [site](https://graphql.org/).


- It is written in Python 3.8.
- It is stored on AWS CodeArtifact which ensures
third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.
- data.all base image for Lambda functions is an AWS approved Amazon Linux
base image, and does not rely on Dockerhub. Docker images are built with
AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

The GraphQL, backend or API Handler Lambda delegates AWS SDK calls and CDK deployment operations to:

1. Short Running Asynchronous Tasks Processor or "Worker"  to AWS Lambda
2. Long Running Background Tasks Processor to ECS Fargate

### AWS Lambda - Short Running Asynchronous Tasks Processor or "Worker" Lambda

The Worker Lambda function performs AWS SDK calls for short running tasks.
The API Handler Lambda and this Worker Lambda functions communicate through a message queue using a SQS queue.

- It is written in Python 3.8.
- It is stored on AWS CodeArtifact which ensures
third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.
- data.all base image for Lambda functions is an AWS approved Amazon Linux
base image, and does not rely on Dockerhub. Docker images are built with
AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

### Amazon SQS FIFO Queue

data.all uses Amazon SQS FIFO queue as a messaging mechanism between
"API Handler" Lambda function and the short running AWS tasks Worker Lambda
function.

- Amazon SQS queue is running outside of the VPC. 
- Amazon SQS queue is encrypted with AWS KMS key with enabled
rotation.

### ECS Fargate - Long Running Background Tasks Processor
data.all uses ECS tasks to perform long running tasks or
scheduled tasks. 

One of the tasks performed by ECS is the creation of CDK stacks in the linked environments' accounts.

- data.all ECS backend service docker images are built with AWS
CodePipeline and stored on AWS CodeArtifact which ensures third party
libraries availability, encryption using AWS KMS and auditability
through AWS CloudTrail.

- Docker images: data.all base image for ECS backend service is an AWS approved Amazon
Linux base image, and does not rely on Dockerhub. Docker images are
built with AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

### Amazon Aurora
data.all uses Amazon Aurora serverless – PostgreSQL version to persist the application metadata. For example, for
each data.all concept (data.all environments, datasets...) there is a table in the Aurora database. Additional tables
support the application business logic.

- Aurora database is encrypted with AWS KMS key with enabled rotation.
- Aurora database is running inside a VPC and private subnets.
- It is accessible only by data.all resources like Lambda functions and ECS tasks
through security groups inbound rules.

  
### Amazon OpenSearch
data.all uses Amazon OpenSearch to index datasets information
for optimal search experience on the catalog.

- Amazon OpenSearch cluster is running inside a VPC and private
subnets.
- It is accessible only by data.all resources like Lambda
functions and ECS tasks through security groups inbound rules.
- It is encrypted at rest with AWS KMS customer managed key (CMK).

### AWS Lambda OpenSearch Handler
This Lambda function performs operations on the Catalog OpenSearch cluster: queries, upserts, deletes of items.

- It is written in Python 3.8.
- It is stored on AWS CodeArtifact which ensures
third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.
- data.all base image for Lambda functions is an AWS approved Amazon Linux
base image, and does not rely on Dockerhub. Docker images are built with
AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.


### Monitoring with CloudWatch and CloudWatch RUM
As part of the deployment, data.all deploys monitoring AWS resources with CDK and ultimately in CloudFormation. These include
AWS CloudWatch Alarms on the infrastructure: on Aurora DB, on the OpenSearch cluster, on API errors...
Operation teams can subscribe to a topic on Amazon SNS to receive near
real time alarms notifications when issues are occurring on the
infrastructure.

Additionally, we enable [CloudWatch RUM](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-RUM.html) to 
collect and view client-side data about your web application 
performance from actual user sessions in near real time.



## Linked Environments <a name="environment"></a>


### Overview

An environment on data.all is an AWS account that verifies two
conditions:

1.  pivotRole IAM role is created on the AWS account and trusts data.all deployment account.
2.  AWS account is bootstrapped with CDK and is trusting data.all deployment account.

### pivotRole ExternalId

Each data.all environment must have an AWS IAM role named
**pivotRole** that trusts data.all's deployment account, so that
it could assume that role and do AWS operations like list AWS Glue
database tables etc\...

The **pivotRole** is secured with an **externalId** that the
pivot role must be created with otherwise the STS AssumeRole operation
will fail. This is a recommended pattern from AWS
see [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html) to
grant access to external AWS accounts.

The **externalId** is created with the data.all infrastructure and is
stored on AWS Secretsmanager encryted with a KMS key. Only users with
access to data.all can see and use the externalId.

![](assets/vpconly/image6.png#zoom#shadow)

### pivotRole Template
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
              - 'cloudformation:ListStackResources'
              - 'cloudformation:DescribeStackResource'
            Resource:
              - !Sub 'arn:aws:cloudformation:*:${AWS::AccountId}:stack/${EnvironmentResourcePrefix}*/*'
              - !Sub 'arn:aws:cloudformation:*:${AWS::AccountId}:stack/CDKToolkit/*'
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

## data.all Resources Security

### Overview

data.all resources are the objects created by the users through data.all
UI or API like datasets, notebooks, dashboards... We will discuss below
the security of the most critical data.all resources.

### Datasets

data.all stack deploys the AWS resources on the figures below:

![](assets/vpconly/image7.png#zoom#shadow)

![](assets/vpconly/image8.png#zoom#shadow)

#### Security Configuration

Following security means are configured automatically for each dataset:

-   Encryption: Datasets are protected by AWS Managed KMS Keys, one key is generated for each Dataset.

-   Traceability: All access to data is logged through AWS CloudTrail logs

-   Traceability: All SQL queries from EMR, Redshift, Glue Jobs, Athena is automatically captured through Lake Formation

#### Networking Configuration

-   Glue jobs related to the dataset are by default running outside the VPC.

#### Data sharing

All data sharing is READ ONLY. When a dataset owner decides to share a
table, or a prefix with another Team, this will automatically update the
stack (infrastructure as code) of the dataset.

For structured data:

-   The underlying Lake Formation tables will have an additional Readonly Grant, allowing the remote account to Select and List the data for the shared table

For unstructured data:

-   The underlying S3 Bucket will be updated with an additional Policy granting read only access to the remote account on the underlying S3 Prefix

#### Traceability & Forensic

All (federated) users of a data.all Environment (AWS Account) can access
the dataset resource below:

-   S3 data hosted on this account

-   S3 Data (prefixes) shared by other accounts

-   data managed by Lake Formation created on this Environment

-   tables managed by Lake Formation shared with the Environment

#### Extensibility

Any security requirement can be fully automated through adding resources
to the stacks that define the dataset resources. This provides security
team with simple ways to add any security mechanism at the scale of the
data lake, as opposed to applying security on a project basics.

### Warehouses

Warehouse are Amazon Redshift Clusters created or imported by data.all
that allows data teams to implement secure, automated, data warehousing
including loading data from S3 through Spectrum

#### AWS Resources

A warehouse in data.all is mapped to

  |Service|           Resource|   Description|
  |-----------------| ---------- |----------------------------------------------|
  |Redshift |         Cluster  |  Amazon Redshift cluster for data warehousing|
  |KMS|               Key |       Key encryption used by the Redshift cluster|
  |Secrets Manager|   Secret|     Stores Redshift cluster user credentials|

All resources are created automatically on an AWS Account/Region

**Security Configuration**

Following security means are configured automatically for each Redshift
cluster:

-   Encryption: Amazon Redshift Cluster is encrypted with KMS.

-   Traceability: All access to data is logged through AWS CloudTrail
    logs

-   Networking Configuration: Redshift cluster is deployed only within a
    private subnet

### Notebooks

Notebooks in data.all are a concept that allows Data Scientists to build
machine learning models using Amazon Sagemaker Studio:

#### AWS Resources

A notebook in data.all is mapped to

  |Service|     Resource|   Description|
  |----------- |---------- |-------------------------------|
  |SageMaker|   Instance|   SageMaker Studio user profile|

All resources are created automatically on an AWS Account/Region

**Security Configuration**

Following security means are configured automatically for each dataset:

-   Traceability: All access to data is logged through AWS CloudTrail
    logs

**Networking Configuration**

Sagemaker studio is running on the VPC and subnets provided by the user.

## Application Security Model

data.all permission model is based on group membership inherited from the
corporate IDP.

Each object in data.all will have

-   A **Creator** with full permissions on the object

-   A **Team** with full permissions on the object, the group is being
    federated with the Corporate IDP

**Organizations**

Organizations are created by a team, and other teams (IDP groups) can be
invited on an organization to link their AWS accounts as data.all
environments.

Only the users belonging to the administrator's team and the invited
teams are allowed to see the organization.

**Environments**

An environment is created by a user and associated with a Team. The team
members are administrators of the environment and they can invite other
teams.

Administrators of the environment can invite other IDP groups to
collaborate on the same environment. Administrators are able to grant
fine grained permissions which will create an IAM role with the same
permissions to access the AWS account.

Only the users belonging to the administrator's team and the invited
teams are allowed to access the underlying AWS account.

**Datasets**

A dataset had one creator with technical permissions on the Dataset
metadata and underlying access to the data in AWS.

One technical admin team with same permissions as the dataset creator

Each Dataset must have a team of stewards (IDP group), granting or
denying access to the dataset items (tables/folders).

Finally, Dataset items can be shared with other environments and teams,
i.e. an another account and an IAM role, federated through corporate
IDP.

when a Table is shared, its shared across AWS account using AWS Lake
Formation cross account table sharing, allowing READ ONLY Access to the
shared table

when a folder is shared, the Bucket Policy of the Dataset is allowing
READ ONLY to the other account, in READ ONLY mode

**Pipelines**

A Pipeline has one creator with technical permissions on the Pipeline
and underlying access to the data in AWS.

one technical admin team with same permissions as the Pipeline creator
that can run the Pipeline from the User Interface or API.

**Dashboards**

A Dashboard has one creator with technical permissions on the Dashboard
and underlying access to the data in AWS.

one technical admin team with same permissions as the Dashboard Creator.



