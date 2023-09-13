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
   - [Frontend Components](#frontend)
   - [Backend Components](#backend)
4. [Linked Environments](#environment)
   - [CDK bootstrap](#cdk)
   - [pivotRole SDKs](#pivotrole)
5. [data.all Resources](#resources)
6. [Permission Model](#permission)

## End-to-end architecture <a name="end"></a>

![archi](img/architecture_complete.drawio.png#zoom#shadow)

## CICD in tooling account <a name="tooling"></a>

data.all infrastructure (in the deployment account(s)) is deployed from the tooling account using AWS CodePipeline.
Cloud resources in 
data.all are defined using the [AWS Cloud Development Kit](https://aws.amazon.com/cdk/) (AWS CDK).
data.all CI/CD was built with cross accounts deployments in mind using AWS CDK pipelines 
[version 2.14.0](https://pypi.org/project/aws-cdk-lib/2.14.0/). 


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
the remaining 10% is for the OpenSearch cluster. Since data.all release v1.5.0 you have the ability to deploy an OpenSearch Serverless cluster instead by specifying the `enable_opensearch_serverless` parameter of the configuration cdk.json file. Check the [Deploy to AWS](./deploy-aws/) section.

![archi](img/architecture_infrastructure.drawio.png#zoom#shadow)

## Frontend Components <a name="frontend"></a>

To fit the requirements of enterprise grade customers, data.all architecture has two variants. Both 
architectures are part of data.all code base and can be configured in the deployment with the 
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
balancer (ALB) deployed on the VPC's private subnet. Data.all static sites are hosted on Amazon ECS using docker containers through nginx server.


The ALB is reachable only from Amazon VPCs and not from the internet. Also, APIs are private and accessible only through VPC endpoints. 
For this kind of architecture, the following resources need to be provisioned as pre-requisite for the deployment:
- Route 53 private hosted zone
- ACM certificate
- For the above you will also need a VPC which needs to be provided as input for the deployment. Check the backend VPC section to review the VPC requirements.

Although it is not a pre-requisite per se, to use this architecture customers need a way to connect with the data.all VPC. Typically,
this is achieved by connecting the VPN to the VPC in data.all.

With the following commands you can create the ACM certificate and Route 53 private hosted zone:
1.	`cd` to empty directory
2.	This command will create your pem and a paraphrase password file: `openssl req -x509 -newkey rsa:4096 -days 1825 -keyout dataallkey.pem -out dataall.pem -addext "subjectAltName=DNS:<YOUR-HOSTED-ZONE-NAME>,DNS:*.<YOUR-HOSTED-ZONE-NAME>"`
3.	This command will create a no password file to load in ACM: `openssl rsa -in dataallkey.pem -out dataallkeynopwd.pem `
4.	`aws route53 create-hosted-zone --name <domain-name> --vpc VPCRegion=<vpc_region>,VPCId=<vpc-id> --caller-reference 07:12:22 --query HostedZone.Id --output text `
5.	`aws acm import-certificate --region us-east-1 --certificate fileb://<filepath to cert> --private-key fileb://<filepath to no password key> --query CertificateArn --output text`

After it is deployed, How do I connect (or simulate the connection) between my VPN and data.all VPC? The following
resources might be helpful for testing and connecting the deployment:
- [Support post](https://aws.amazon.com/premiumsupport/knowledge-center/route53-resolve-with-inbound-endpoint/)
- [Workshop](https://catalog.workshops.aws/networking/en-US/intermediate/3-hybrid-dns/10-hybrid-dns-overview)
- [Reference architecture](https://d1.awsstatic.com/architecture-diagrams/ArchitectureDiagrams/hybrid-dns_route53-resolver-endpoint-ra.pdf)


![](img/architecture_frontend_vpc.drawio.png#zoom#shadow)

- Third party libraries: data.all static sites libraries are stored on AWS CodeArtifact which
ensures third party libraries availability, encryption using AWS KMS and
auditability through AWS CloudTrail.

- Docker images: data.all base image for static sites is an AWS approved Amazon Linux base
image, and does not rely on Dockerhub. Docker images are built with AWS
CodePipeline and stored on Amazon ECR which ensures image availability,
and vulnerabilities scanning.

## Backend Components <a name="backend"></a>

![Screenshot](img/architecture_backend.drawio.png#zoom#shadow)

### Backend VPC

#### Created by data.all
If we do not provide a VPC ID for the different infrastructure accounts in the deployment configuration (aka cdk.json), 
data.all creates its own VPC in the account where it is set up, with usual configuration.
All backend compute is hosted in the **private subnets**, and communicates with AWS Services through a **NAT Gateway**.

All data.all Lambda functions and ECS tasks are running inside this VPC and in private
subnets. 

![Screenshot](img/architecture_vpc.drawio.png#zoom#shadow)

#### Created outside of data.all
There are 2 scenarios where we might want to provide our own VPCs:
1) Organization guidelines. In your organization there are certain policies and mechanisms to create VPCs.
2) Frontend needs to be hosted in data.all VPC facing architecture

When providing the VPC, your VPC should resemble the image above.

1. Make sure that it is deployed in at least 2 Availability Zones (AZ)
2. Make sure that it has at least 1 public subnet. Data.all needs to download packages, hence needs public access.
3. Make sure that the private subnets route to a NAT Gateway
4. Make sure that the VPC created does not have an S3 VPC endpoint

Here is a screenshot of the creation of the VPC: 
![Screenshot](img/vpc_setup.png#zoom#shadow)


### Backend AWS API Gateway
data.all backend main entry point is an AWS API Gateway that exposes a
GraphQL API.

- API Gateway is private and not exposed to the internet, it's linked to a
shared VPC endpoint. 
- A resource policy on the API Gateway denies any traffic with a source different than the VPC
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

data.all uses Amazon SQS FIFO queue as a messaging mechanism between the
API Handler Lambda function and the Worker Lambda
function.

- Amazon SQS queue is running outside of the VPC. 
- Amazon SQS queue is encrypted with AWS KMS key with enabled
rotation.

### ECS Fargate - Long Running Background Tasks Processor
data.all uses ECS tasks to perform long running tasks or
scheduled tasks. One of the tasks performed by ECS is the 
creation of CDK stacks in the linked environments' accounts.

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

By default, Amazon OpenSearch Service cluster is created, however users have the ability to use Amazon OpenSearch
Serverless collection instead by enabling a corresponding feature flag in `cdk.json`.

- Amazon OpenSearch cluster is running inside a VPC and private
subnets.
- If using Amazon OpenSearch Serverless collection, it is only accessible through OpenSearch
Serverless–managed VPC endpoints.
- It is accessible only by data.all resources like Lambda
functions and ECS tasks thanks to enforced security groups inbound rules in case of OpenSearch cluster, or access
policies in case of Amazon OpenSearch Serverless.
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


### Observability with CloudWatch and CloudWatch RUM
As part of the deployment, data.all deploys observability AWS resources with CDK and ultimately in CloudFormation. These include
AWS CloudWatch Alarms on the infrastructure: on Aurora DB, on the OpenSearch cluster, on API errors...
Operation teams can subscribe to a topic on Amazon SNS to receive near
real time alarms notifications when issues are occurring on the
infrastructure.

Additionally, if we enabled [CloudWatch RUM](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-RUM.html) 
in the config.json file when we deployed data.all we will be able to
collect and view client-side data about your web application 
performance from actual user sessions in near real time.



## Linked Environments <a name="environment"></a>

Environments are workspaces where one or multiple teams can work. They are the door between our users in data.all and AWS, that is
why we say that we "link" environments because we link each environment to **ONE** AWS account, in one specific region.
Under each environment we create other data.all resources, such as datasets, pipelines and notebooks. 

For the deployment of 
CloudFormation stacks we call upon a CDK trust policy between the Deployment account and the Environment account. 
As for the SDK calls, from the deployment account we assume a certain IAM role in the environment accounts, the pivotRole.

Consequently, to link one AWS account with an environment, the account must verify two
conditions:

1. AWS account is bootstrapped with CDK and is trusting data.all deployment account.
2. pivotRole IAM role is created on the AWS account and trusts data.all deployment account.


![archi](img/architecture_linked_env.drawio.png#zoom#shadow)


### CDK bootstrap <a name="cdk"></a>
We need to bootstrap the environment account to provision resources the AWS CDK needs to perform the deployment of
environments, datasets, pipelines and other data.all resources. 

Run the following command with AWS credentials of the environment account: 
```bash
cdk bootstrap --trust <deployment-account-id> -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://<environment-account-id>/<environment-account-region>
```

Note that we added some parameters to the bootstraping command, as appears in the 
[documentation](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html):
- `--trust`: lists the AWS accounts that may deploy into the environment being bootstrapped. Use this flag when bootstrapping an environment that a CDK Pipeline in another environment will deploy into. The account doing the bootstrapping is always trusted.
- `--cloudformation-execution-policies`: specifies the ARNs of managed policies that should be attached to the 
deployment role assumed by AWS CloudFormation during deployment of your stacks. 

  
### pivotRole <a name="pivotrole"></a>

Each data.all environment must have an AWS IAM role named
**pivotRole** that trusts data.all's deployment account, so that
it could assume that role and do AWS operations like list AWS Glue
database tables etc...

The pivotRole is secured with an **externalId** with whom it must be created. 
Otherwise, the STS AssumeRole operation
will fail. This is a recommended pattern from 
[AWS](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html) to
grant access to external AWS accounts.

The externalId is created with the data.all infrastructure and is
stored on **AWS Secrets Manager** encrypted with a KMS key. Only users with
access to data.all can see and use the externalId.

From the data.all UI we can download a CloudFormation template of the pivotRole and deploy it in our business account. 
Alternatively, you can access this template directly from the 
[Github repository/deploy](https://github.com/awslabs/aws-dataall/blob/main/deploy/pivot_role/pivotRole.yaml). 


## data.all Resources <a name="resources"></a>

data.all resources are the objects created by the users through data.all
UI or API like datasets, notebooks, dashboards... We will discuss below
the security of those data.all resources that have a CloudFormation stack associated.

### Datasets

They are created inside a data.all environment, thus the dataset stack is deployed in the environment linked AWS
account and region. When we create a data.all dataset we are deploying the following resources (not only):


  | Service         |           Resource|   Description|
-----------------|-----------------| ---------- |----------------------------------------------|
  | S3               |         Bucket  |  Amazon S3 Bucket where the data is stored|
  | KMS             |               Key |       Key encryption used to encrypt the dataset S3 Bucket|
  | IAM             |               Role |       Role for direct link access to the dataset S3 Bucket|
  | Glue |   Database|     Glue database that holds the dataset tables|

We also have the option to **import** a dataset, in such case we can reuse an existing S3 Bucket and Glue database.


**Security and Networking configuration**:

-   Encryption: Datasets are protected by AWS Managed KMS Keys, one key is generated for each Dataset.
-   Traceability: All access to data is logged through AWS CloudTrail logs
-   Traceability: On our structured data, all SQL queries from EMR, Redshift, Glue Jobs, Athena is automatically captured through Lake Formation.
-   Glue jobs related to the dataset are by default running outside the VPC.


### Notebooks

Notebooks in data.all are a concept that allows Data Scientists to build
machine learning models using Amazon Sagemaker Studio. They are created inside a data.all environment, 
thus the notebook stack is deployed in the environment linked AWS
account and region. It includes:

  |Service|     Resource|   Description|
  |----------- |---------- |-------------------------------|
  |SageMaker|   Instance|   SageMaker Studio user profile|


**Security and Networking configuration**:

- Traceability: All access to data is logged through AWS CloudTrail
    logs.
- Sagemaker studio is running on the VPC and subnets provided by the user.

## Permission Model <a name="permission"></a>

data.all permission model is defined at group level not at user level.
We define permissions for a group, this can be a Cognito group or a group coming from your IdP.
The permissions defined by data.all on the group affect all of its members.

Each object in data.all will have an **object-Team** with full permissions on the object, 
it corresponds to a Cognito group that is typically
federated with the Corporate IdP. 


### Tenant group
data.all has a tenant group which correspond to a group from Cognito or from your
IdP that has the right to manage high level application (tenant)
permissions for all IdP groups integrated with data.all.

This super user's group maps to a group from your IdP that's by default
named "DAAdministrators". Any user member of this group will be
able to:

- create organizations
- manage tenant permissions on onboarded groups (IdP groups).

### Organizations

Organizations are created by the tenant group or by a group granted "create-organization" permissions. An organization
is linked to a group, this is the organization-Team. 
Other Teams (IdP groups) can be
invited to an existing organization to link their AWS accounts as data.all
environments.

Only the users belonging to the organization-Team and the invited
Teams are allowed to see the organization.

### Environments

An environment is created by a user and associated with a Team. Members of this environment-Team can invite other
Teams, other IdP groups. Members of the environment-Team are able to grant
fine-grained permissions to the invited teams, which will create an IAM role with the corresponding
permissions to access the AWS account.

Only the users belonging to the environment-Team and the invited
Teams are allowed to access the underlying AWS account. For the latest, they access the AWS Account assuming
the IAM role with the fine-grained permissions set by the environment-Team.

### Datasets and data access

A dataset is created by a user and associated to an environment and team, which becomes the dataset-Team.
Members of this team have UI permissions on the Dataset
metadata and underlying access to the data in AWS, that is:
- access to dataset metadata (e.g. AWS information) from the data.all UI
- direct link access to the dataset S3 Bucket from the data.all UI
- assuming their environment created IAM role, they can access the dataset S3 Bucket
- assuming their environment created IAM role, they can access the data with all AWS Services integrated with Glue Catalog/Lake Formation


Users that are NOT members of the dataset-Team CANNOT perform the above listed actions on the dataset data.

**Note**: Any security requirement can be fully automated through adding resources
to the stacks that define the dataset resources. This provides security
team with simple ways to add any security mechanism at the scale of the
data lake, as opposed to applying security on a project basics.


### Data sharing
Each Dataset must have at least one Team of stewards (IdP group), handling sharing requests
to the dataset items (tables/folders). We can define our dataset-Team as steward and on top, add additional
Teams that will support us in the granting/revoking of data access.

Users request access on behalf of an environment and team, then a member of the Stewards teams can either
accept or deny the request. Dataset items can be shared with other environments and teams. This effectively means
that we perform cross-account data sharing to a chosen IAM role.

**Note**: Once the share request is accepted and processed, the specified Team members get access to the requested items.
That means that data is granted for a Team, not for a user.

Dataset items are Tables and Folders:
- Tables, for structured data: The underlying Glue tables secured by Lake Formation will have an 
additional READ ONLY Grant, allowing the remote account to Select and List the data for the shared table.

- Folders, for unstructured data: The underlying S3 Bucket will be updated with an 
additional Policy granting READ ONLY access to the remote account on the underlying S3 Prefix.

![archi](img/architecture_sharing.drawio.png#zoom#shadow)

**Sharing remarks**
- sharing actions, either Lake Formation grants or CDK updates of the S3 bucket policy, are performed by data.all backend. 
Users of data.all don't have access to the code that performs the share.
- Data is shared, it is not copied between accounts.
- Since table sharing is based on Lake Formation, it is subtle to Lake Formation service limitations. e.g. cross-region sharing.

### Notebooks

A Notebook has a notebook-Team with UI permissions on the Notebook
and underlying access to the data in AWS.

### Pipelines

A Pipeline has a pipeline-Team with UI permissions on the Pipeline
and underlying access to the data in AWS.

### Dashboards

A Dashboard has a dashboards-Team with UI permissions on the Dashboard
and underlying access to the data in AWS.

