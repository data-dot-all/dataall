---
layout: default
homePage: false
title: Security
permalink: /security/
---


DATAHUB enforces security best practices on AWS Resources that it creates, in terms
of encryption, access control and traceability.

## **Authentication**

Users in DATAHUB are authenticated against AWS Cognito
In a typical step of DATAHUB, Cognito is federated with a  corporate Identity Provider, such
as Okta or Active Directory (including Azure AD 365)

!!! note
    Saml2 and Oauth federation are supported.

DATAHUB doesn't have a user store and does not create or manage groups.
It relies only on information provided by IDP as username, email, groups
etc...

![Screenshot](assets/auth.png#zoom#shadow){: style="width:80%"}


## **Static Sites Networking & Security**

### **Overview**

DATAHUB solution comes with 3 different static sites that are served to
the users:

1.  DATAHUB User Interface: React JS application that integrates with
    AWS Cognito for user authentication, which is also the main UI.

2.  DATAHUB development guide: Static HTML documents generated from
    markdown files using Mkdocs library available to all users having
    access to the server hosting the documentation.

3.  DATAHUB user guide: Static HTML documents generated from markdown
    files using Mkdocs library available to all users having access to
    the server hosting the documentation.

### **Hosting**

DATAHUB static sites are hosted on Amazon ECS using docker containers:

![](assets/vpconly/image3.png#zoom#shadow)

### **Networking**

DATAHUB static sites are deployed on an AWS internal application load
balancer (ALB) deployed on the VPC's private subnet. This ALB is
reachable only from Amazon VPCs and not from the internet.

### **Security**

#### **Third party libraries**

DATAHUB static sites libraries are stored on AWS CodeArtifact which
ensures third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.

#### **Docker images**

DATAHUB base image for static sites is an AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.

## **Backend Networking & Security**
### **Overview**

DATAHUB backend main entry point is an AWS API Gateway that exposes
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

DATAHUB relies on lambda functions for API Authorization, and business
logic.

#### **Networking**

All DATAHUB lambda functions are running inside a VPC and private
subnets.

#### **Security**

#### **Third party libraries**

DATAHUB Lambda functions are stored on AWS CodeArtifact which ensures
third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.

#### **Docker images**

DATAHUB base image for Lambda functions is an AWS approved Amazon Linux
base image, and does not rely on Dockerhub. Docker images are built with
AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

### **ECS services**

DATAHUB uses ECS tasks as microservices to do long running taks or
scheduled tasks.

#### **Networking**

All ECS tasks are running inside a VPC and private subnets.

#### **Security**

#### **Third party libraries**

DATAHUB ECS backend service docker images are built with AWS
CodePipeline and stored on AWS CodeArtifact which ensures third party
libraries availability, encryption using AWS KMS and auditability
through AWS CloudTrail.

#### **Docker images**

DATAHUB base image for ECS backend service is an AWS approved Amazon
Linux base image, and does not rely on Dockerhub. Docker images are
built with AWS CodePipeline and stored on Amazon ECR which ensures image
availability, and vulnerabilities scanning.

### **Aurora Serverless Database**

DATAHUB uses Aurora serverless database to store model information like
datasets, environments...

#### **Networking**

Aurora database is running inside a VPC and private subnets, and is
accessible only by DATAHUB resources like Lambda functions and ECS tasks
through security groups inbound rules.

#### **Security**

Aurora database is encrypted with AWS KMS key with enabled rotation.

### **Amazon ElasticSearch cluster**

DATAHUB uses Amazon ElasticSearch cluster to index datasets information
for optimal search experience on the catalog.

#### **Networking**

Amazon ElasticSearch cluster is running inside a VPC and private
subnets, and is accessible only by DATAHUB resources like Lambda
functions and ECS tasks through security groups inbound rules.

#### **Security**

Amazon ElasticSearch cluster is encrypted with AWS KMS key with enabled
rotation.

### **Amazon SQS FIFO Queue**

DATAHUB uses Amazon SQS FIFO queue as a messaging mechanism between
backend API Lambda functions and the short running AWS tasks Lambda
function.

#### **Networking**

Amazon SQS queue is running outside of the VPC.

#### **Security**

Amazon SQS queue is encrypted with AWS KMS key with enabled
rotation.

## **CI/CD Pipeline Networking & Security**

### **Overview**

DATAHUB infrastructure is deployed using AWS CodePipeline. DATAHUB CI/CD
was built with cross accounts deployments in mind using AWS CDK
pipelines.

![](assets/vpconly/image5.png#zoom#shadow)

#### **Networking**

AWS CodeBuild projects part of the CI/CD pipeline are running inside a
VPC and private subnets.

#### **Security**

#### **Third party libraries**

DATAHUB dependencies are stored on AWS CodeArtifact which ensures third
party libraries availability, encryption using AWS KMS and auditability
through AWS CloudTrail.

The quality gate stage of the CI/CD pipeline scans third party libraries
for vulnerabilities using safety and bandit python libraries.

#### **Docker images**

DATAHUB base image for all components is AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.

#### **Aurora serverless database**

Integration tests Aurora serverless database is encrypted with KMS and
has rotation enabled. Security groups of the database is allowing
Codebuild projects only to access the database.

## **DATAHUB Environments security**

### **Overview**

An environment on DATAHUB is an AWS account that verifies two
conditions:

1.  datahubPivotRole IAM role is created on the AWS account and trusts DATAHUB deployment account.
2.  AWS account is bootstrapped with CDK and is trusting DATAHUB deployment account.

### **DATAHUB Pivot Role ExternalId**

Each DATAHUB environment must have an AWS IAM role named
**datahubPivotRole** that trusts DATAHUB's deployment account, so that
it could assume that role and do AWS operations like list AWS Glue
database tables etc\...

The **datahubPivotRole** is secured with an **externalId** that the
pivot role must be created with otherwise the STS AssumeRole operation
will fail. This is a recommended pattern from AWS
see [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html) to
grant access to external AWS accounts.

The **externalId** is created with the DATAHUB infrastructure and is
stored on AWS Secretsmanager encryted with a KMS key. Only users with
access to DATAHUB can see and use the externalId.

![](assets/vpconly/image6.png#zoom#shadow)

### **DATAHUB Pivot Role Template**
`````yaml
AWSTemplateFormatVersion: 2010-09-09
Description: IAM Role used by datahub platform to run AWS short running tasks
Parameters:
  DatahubAwsAccountId:
    Description: AWS AccountId of the datahub environment
    Type: String
  DatahubExternalId:
    Description: ExternalId to secure datahub assume role
    Type: String
Resources:
  DatahubPrivotRole:
    Type: 'AWS::IAM::Role'
    Properties:
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
                - !Ref DatahubAwsAccountId
            Action:
              - 'sts:AssumeRole'
            Condition:
              StringEquals:
                'sts:ExternalId': !Ref DatahubExternalId
      RoleName: datahubPivotRole
      Path: /
      Policies:
        - PolicyName: DatahubInlinePolicy
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Sid: DatahubFullPermissions
                Action:
                  - 'sns:*'
                  - 'states:*'
                  - 's3:*'
                  - 'redshift-data:*'
                  - 'redshift:*'
                  - 'logs:*'
                  - 'cloudformation:*'
                  - 'sqs:*'
                  - 'athena:*'
                  - 'glue:*'
                  - 'iam:Get*'
                  - 'iam:List*'
                  - 'secretsmanager:*'
                  - 'kms:*'
                  - 'ssm:*'
                  - 'lambda:*'
                  - 'ec2:*'
                  - 'quicksight:*'
                  - 'kinesis:*'
                  - 'lakeformation:*'
                  - 'ram:*'
                  - 'sts:*'
                  - 'cloudwatch:*'
                  - 'sagemaker:*'
                Effect: Allow
                Resource: '*'
Outputs:
  DatahubPivotRoleOutput:
    Description: Datahub Platform Pivot Role
    Value: DatahubPivotRole
    Export:
      Name: !Sub '${AWS::StackName}-DatahubPivotRole'

`````

## **DATAHUB Resources Security**

### **Overview**

DATAHUB resources are the objects created by the users through DATAHUB
UI or API like datasets, notebooks, dashboards... We will discuss below
the security of the most critical DATAHUB resources.

### **Datasets**

DATAHUB stack deploys the AWS resources on the figures below:

![](assets/vpconly/image7.png#zoom#shadow)

![](assets/vpconly/image8.png#zoom#shadow)

#### **Security Configuration**

Following security means are configured automatically for each dataset:

-   Encryption: Datasets are protected by AWS Managed KMS Keys, one key is generated for each Dataset.

-   Traceability: All access to data is logged through AWS CloudTrail logs

-   Traceability: All SQL queries from EMR, Redshift, Glue Jobs, Athena is automatically captured through Lake Formation

#### **Networking Configuration**

-   Glue jobs related to the dataset are by default running outside the VPC.

#### **Data sharing**

All data sharing is READ ONLY. When a dataset owner decides to share a
table, or a prefix with another Team, this will automatically update the
stack (infrastructure as code) of the dataset.

For structured data:

-   The underlying Lake Formation tables will have an additional Readonly Grant, allowing the remote account to Select and List the data for the shared table

For unstructured data:

-   The underlying S3 Bucket will be updated with an additional Policy granting read only access to the remote account on the underlying S3 Prefix

#### **Traceability & Forensic**

All (federated) users of a DATAHUB Environment (AWS Account) can access
the dataset resource below:

-   S3 data hosted on this account

-   S3 Data (prefixes) shared by other accounts

-   data managed by Lake Formation created on this Environment

-   tables managed by Lake Formation shared with the Environment

#### **Extensibility**

Any security requirement can be fully automated through adding resources
to the stacks that define the dataset resources. This provides security
team with simple ways to add any security mechanism at the scale of the
data lake, as opposed to applying security on a project basics.

### **Warehouses**

Warehouse are Amazon Redshift Clusters created or imported by DATAHUB
that allows data teams to implement secure, automated, data warehousing
including loading data from S3 through Spectrum

#### **AWS Resources**

A warehouse in DATAHUB is mapped to

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

### **Notebooks**

Notebooks in DATAHUB are a concept that allows Data Scientists to build
machine learning models using Amazon Sagemaker Studio:

#### **AWS Resources**

A notebook in DATAHUB is mapped to

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

## **Application Security Model**

DATAHUB permission model is based on group membership inherited from the
corporate IDP.

Each object in DATAHUB will have

-   A **Creator** with full permissions on the object

-   A **Team** with full permissions on the object, the group is being
    federated with the Corporate IDP

**Organizations**

Organizations are created by a team, and other teams (IDP groups) can be
invited on an organization to link their AWS accounts as DATAHUB
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
