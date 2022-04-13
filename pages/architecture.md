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

data.all infrastructure is fully automated using AWS (Cloud Development
Kit), and it comes with a CI/CD pipeline for integrating and deployment
data.all code base when changes are introduced.

Deployment task can be achieved running 3 commands and the
infrastructure can take 3 hours to be up and running on AWS.

![archi](img/architecture_tooling.drawio.png#zoom#shadow)

## Infrastructure in deployment account(s) <a name="infrastructure"></a>
Infrastructure is deployed by the 
data.all can be best understood when compared to a <span style="color:#2074d5">**classical 3-tier application**</span>,
implemented using mostly AWS serverless services.
As in classical web application the three layers of data.all are:

1. Presentation layer (Amazon Cloudfront OR Amazon Application Load Balancer)
2. API layer:
    - Client (AWS API Gateway)
    - Server (AWS Lambda)
3. Persistence layer (Amazon Aurora serverless -- Postgres version)

The code and the architecture <span style="color:#2074d5">**decouples**</span> the data.all business logic (CRUD)
from the AWS logic and processing. To achieve this decoupling, the web application delegates any AWS related tasks to two components:

4. Long Running Background Tasks Processor (Amazon ECS Fargate)
5. Short Running Asynchronous Tasks Processor (AWS Lambda)

data.all infrastructure runs <span style="color:#2074d5">**90% on serverless**</span> services in a private VPC, 
the remaining 10% are for the OpenSearch cluster that is not serverless... yet!

![archi](img/architecture_deployment.drawio.png#zoom#shadow)

## Frontend Components <a name="frontend"></a>

To fit the requirements of enterprise grade customers, data.all architecture has two variants. Both 
architectures are part of data.all code base and can be configured with in the deployment with the 
`internet_facing` parameter of the configuration cdk.json file.

- Internet facing architecture
- VPC facing architecture

### Internet facing architecture
This architecture relies on AWS services living outside the VPC like S3 and CloudFront for data.all UI and documentation hosting.
Backend APIs are public and can be reached from the internet. 
Internet facing services are protected with AWS Wep Application Firewall (WAF).

![](img/architecture_frontend_internet.drawio.png#zoom#shadow)

#### Users Authentication
Amazon Cognito is used to manage user authentication. It can be configured to be **federated with an external IDP**, in which case Cognito acts as a simple proxy,
abstracting the different Idp providers protocols.


#### User Interface and Documentation
data.all UI and documentation follow static websites pattern on AWS with CloudFront used as the 
Content Delivery Network (CDN).
CloudFront is protected  by Web Application Firewall (WAF) on top of S3 encrypted buckets hosting the sites assets.


The frontend code is a **React application**, its code is bundled using React 
create-react-app utility, and saved to S3 as the Cloudfront distribution origin.


### VPC facing architecture
In this architecture, data.all static sites are deployed on an AWS internal application load
balancer (ALB) deployed on the VPC's private subnet. This ALB is
reachable only from Amazon VPCs and not from the internet.
Also, APIs are private and accessible only through VPC endpoints.

![](img/architecture_frontend_vpc.drawio.png#zoom#shadow)


## Backend Components <a name="backend"></a>

### VPC

data.all creates its own VPC in the account where it is set up, with usual configuration.
All compute is hosted in the **private subnets**, and communicates with AWS Services through a **NAT Gateway**.

![Screenshot](img/architecture_vpc.drawio.png#zoom#shadow)

### Backend API Gateway
API Gateway is used to host the data.all backend API, and exposes a **GraphQL API**.
This API is authenticated using **JWT Tokens** from **Cognito** service.
![Screenshot](assets/apigw.png#zoom#shadow)


### Lambda Functions

data.all is using three AWS Lambda functions for the application logic:

1. The **Backend** Lambda function that implements the business logic.
2. The **AWS Worker** lambda function that performs AWS SDK calls for short running tasks.
3. The  **Authorizer** lambda function that performs authorization checks.
4. The  **Metadata** lambda that exposes api to update datasets metadata.

#### Backend and Metadata Lambda Functions

!!!abstract "API and AWS SDK call decoupling"
    The **Backend** and **Metadata** functions does not perform AWS API calls, but process incoming GraphQL queries and delegates AWS SDK calls to:

1. **AWS Worker** lambda function
2. **CDK Service** running on AWS Fargate service (see below).

![Screenshot](assets/graphql-lambda.png#zoom#shadow)

Backend and worker functions communicate through a **message queue** using **SQS queue**.

![Screenshot](assets/worker-lambda.png#zoom#shadow)

#### AWS Worker Lambda Function
The worker function is the background worker process explained in the eagle-eye view section, and is the one performing short and / or long running tasks against the AWS API.

#### AWS Authorizer Lambda Function
The last Lambda function is the authorizer, that is in charge of authentications:
1.	Validating JWT Token received by the UI
2.	Validating API keys received through programmatic requests to the service

!!!abstract "Everything Python"
    All Lambda functions are coded in **Python 3.8**.

### ECS Fargate (Serverless)

ECS Fargate is used to host a **web service only accessible from the private VPC subnets**
that exposes an API to create Cloudformation stacks using the **AWS CDK (Cloud Development Kit)** framework.

!!!abstract "CDK superpowers"
    Most of the resources created on AWS by data.all are created through this service and are instantiated using **CloudFormation stacks generated by CDK**.

![Screenshot](assets/fargate.png#zoom#shadow)

### Aurora
data.all uses **Amazon Aurora (serverless – PostgreSQL version)** to persist the application data
that is encrypted at rest with **AWS KMS customer managed key (CMK)**.

![Screenshot](assets/db.png#zoom#shadow)


### Amazon ElasticSearch
data.all uses **Amazon Elastic Search (ES)** to index the datasets metadata for a better search experience.
The ES cluster is encrypted at rest with **AWS KMS customer managed key (CMK)**.




## Operation teams can subscribe to a topic on Amazon SNS to receive near
real time alarms notifications when issues are occurring on the
infrastructure (DDoS attack, Database session limits...)