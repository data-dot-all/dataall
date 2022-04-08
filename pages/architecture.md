---
layout: default
homePage: false
title: Architecture
permalink: /architecture/
---
# **Architecture**

## Overview

data.all can be best understood when compared to a classical 3-tier application,
implemented using mostly AWS serverless services.
The three layers of data.all are no different from a classical web application layers which are:

1.	**Presentation layer** (Amazon Cloudfront)
2.	**API layer** :
    - **Client**  (AWS API Gateway)
    - **Server** (AWS Lambda)
3. **Persistence layer** (Amazon Aurora serverless -- Postgres version)

The code and the architecture **decouples** the data.all business logic (CRUD)
from the AWS logic and processing. To achieve this decoupling the Web application delegates any AWS related tasks to two components:

4. **Long Running Background Tasks Processor**(Amazon ECS Fargate) : this containerized application exposes a REST API that runs AWS CloudFormtion Stacks
5. **Short Running Asynchronous Tasks Processor** (AWS Lambda) : this lambda runs tasks sent by the web application
to a message queue (over SQS) and that performs short or long-running tasks against AWS Apis (e.g. : list Glue tables ).

!!!abstract " 10% not serverless !"
    data.all infrastructure runs 90% on serverless services in a private VPC, the remaining 10% are for the **ElasticSearch cluster** that is not serverless... **yet !**

data.all architecture is optimized to fit the requirements of enterprise grade customers. It comes with two variants:

1. **Internet facing architecture**
2. **VPC facing architecture**

### Internet facing architecture
This architecture relies on AWS services living outside the VPC like S3 and CloudFront for data.all UI and doncumentation hosting.
Also, The backend APIs are public and can be reached from the internet.

Internet facing services are protected with **AWS Wep Application Firewall (WAF)**.

![Screenshot](assets/internetFacingArchitecture.png#zoom#shadow)

### VPC facing architecture
In this architecture, data.all static sites are deployed on an AWS internal application load
balancer (ALB) deployed on the VPC's private subnet. This ALB is
reachable only from Amazon VPCs and not from the internet.
Also, APIs are private and accessible only through VPC endpoints.

![](assets/vpconly/vpcfacing.png#zoom#shadow)

!!!success "Pro Tip"
    **Both architectures are part of data.all code base and can be configured with AWS CDK**

### Users Authentication
Amazon Cognito is used to manage user authentication. It can be configured to be **federated with an external IDP**, in which case Cognito acts as a simple proxy,
abstracting the different Idp providers protocols.
![Screenshot](assets/auth.png#zoom#shadow)

### data.all User Interface and Documentation
data.all UI and documentation follow static websites pattern on AWS with a Cloudfront distribution protected
by Web Application Firewall (WAF) on top of S3 encrypted buckets hosting the sites assets.

Authentication is managed by Cognito that offers multiple identity providers integrations.

![Screenshot](assets/staticpart.png#zoom#shadow)
### Cloudfront

Cloudfront is used as the Content Delivery Network (CDN) for the data.all User Interface.

The frontend code is a **React application**, its code is bundled using React create-react-app utility, and saved to S3 as the Cloudfront distribution origin.

![Screenshot](assets/cloudfront.png#zoom#shadow)
## Backend Components Dive Deep

### VPC

data.all creates its own VPC in the account where it is set up, with usual configuration.

!!! danger "Private Subnets ONLY !"
    All compute is hosted in the **private subnets**, and communicates with AWS Services through a **NAT Gateway**.

![Screenshot](assets/vpc.png#zoom#shadow)

### Backend API Gateway
API Gateway is used to host the data.all backend API, and exposes a **GraphQL API**.
This API is authenticated using **JWT Tokens** from **Cognito** service.
![Screenshot](assets/apigw.png#zoom#shadow)

### Metadata API Gateway
API Gateway is used to host the data.all metadata API, and exposes a **GraphQL API**.

This API is authenticated using **IAM** and can be used for a machine to machine access when it comes
to updating datasets metadata.
This API is authenticated using **IAM_AUTH** type.
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

## Deployment and monitoring

data.all infrastructure is fully automated using AWS (Cloud Development
Kit), and it comes with a CI/CD pipeline for integrating and deployment
data.all code base when changes are introduced.

Deployment task can be achieved running 3 commands and the
infrastructure can take 3 hours to be up and running on AWS.

Operation teams can subscribe to a topic on Amazon SNS to receive near
real time alarms notifications when issues are occurring on the
infrastructure (DDoS attack, Database session limits...)

## Infrastructure cost

Running data.all in production costs around **1000\$** per month for
around 50 active users, this is an estimation that may vary if you
introduce change to the data.all's default infrastructure or you have
more active users for you may need to scale the resources.

All data.all infrastructure is tagged with a key "Application" and a
value "data.all", adding this tag to AWS Cost Explorer gives a clear
visibility on data.all infrastructure cost separation:

Figure 1: AWS Cost Explorer filtered by **data.all** tag

### Cost Report example

  |Service                       | Cost (\$)  |
  |------------|----------------|
  |Relational Database Service| 318.378647 |
  |Elasticsearch Service| 237.804468 |
  |EC2-Other| 41.5842477 |
  |CodeBuild | 14.85      |
  |WAF  | 9.01514395 |
  |EC2 Container Registry (ECR)| 3.04734135 |
  |Key Management Service| 1.96205035 |
  |Cognito | 0.3        |
  |CodeArtifact  | 0.29626176 |
  |S3       | 0.24205666 |
  |Secrets Manager | 0.011725   |
  |Lambda     | 0          |
  |API Gateway    | 0          |
  |CloudFront | 0          |
  |EC2-Instances | 0          |
  |EC2-ELB  | 0          |
  |SNS     | 0          |
  |SQS   | 0          |
  |Total  |            **637.771971**|
