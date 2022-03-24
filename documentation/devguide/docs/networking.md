# **NETWORKING**

### **Frontend Requirements**

Frontend of DATAHUB web application is a React Javascript application hosted on an Amazon S3 bucket which is the
origin of an Amazon CloudFront distribution.

**Frontend is internet facing and is protected with AWS Web Application Firewall
service against malicious attacks.**

![Screenshot](assets/cloudfront.png#zoom#shadow)

### **Backend Requirements**
On AWS, the DATAHUB backend infrastructure runs 90% on serverless services in a private VPC, as shown in the following diagram below:

![Screenshot](assets/backend.png#zoom#shadow)

### **Internet Facing Components**

#### **Backend API Gateway**
API Gateway is used to host the DATAHUB backend API, and exposes a **GraphQL API** to the internet and is protected with AWS Web Application Firewall
service against malicious attacks.
This API is authenticated using **JWT Tokens** from **Cognito** service.

#### **Metadata API Gateway**
API Gateway is used to host the DATAHUB metadata API, and exposes a **GraphQL API**.
This API is authenticated using **IAM_AUTH** type.

### **VPC Components**
DATAHUB creates its own VPC in the account where it is set up, with usual configuration.

!!! danger "Private Subnets ONLY !"
    All compute is hosted in the **private subnets**, and communicates with AWS Services through a **NAT Gateway**.

![Screenshot](assets/vpc.png#zoom#shadow)

### **Lambda Functions**

DATAHUB is using three AWS Lambda functions for the application logic:

1. The **Backend** Lambda function that implements the business logic.
2. The **AWS Worker** lambda function that performs AWS SDK calls for short running tasks.
3. The  **Authorizer** lambda function that performs authorization checks.
4. The  **Metadata** lambda that exposes api to update datasets metadata.
5. **Custom resources** needed for the deployment automation.

**Lambda functions run inside the VPC and private subnets, internet connection is provided through
the NAT Gateway**

Lambda functions require networking access to:

* **Aurora database**
* **Elastic Search cluster**

### **ECS Fargate (Serverless)**

ECS Fargate is used to host a **web service only accessible from the private VPC subnets**
that exposes an API to create Cloudformation stacks using the **AWS CDK (Cloud Development Kit)** framework.

**Fargate tasks run inside the VPC and private subnets, the ELB used in front of the ECS tasks in internal facing
only.**

Fargate tasks require networking access to:

* **Aurora database**
* **Elastic Search cluster**

### **Aurora**
DATAHUB uses **Amazon Aurora (serverless – PostgreSQL version)** to persist the application data
that is encrypted at rest with **AWS KMS customer managed key (CMK)**.

**Aurora database run inside the VPC and private subnets.**


### **Amazon ElasticSearch**
DATAHUB uses **Amazon Elastic Search (ES)** to index the datasets metadata for a better search experience.
The ES cluster is encrypted at rest with **AWS KMS customer managed key (CMK)**.

**Amazon ElasticSearch cluster run inside the VPC and private subnets.**
