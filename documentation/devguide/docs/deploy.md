# Deployment

## **Pre-requisites**
You need to have the tools below up and running to proceed with the deployment:

* python 3.8
* virtualenv
* node
* npm
* cdk cli : installed globally `npm install -g aws-cdk`
* aws-cli (v2)
* git client
* Admin AWS Credentials in the default profile
* Linux Box recommended
* Docker

**Install Python PyGreSQL**

**PyGreSQL** library is used to manage the connection pool to PostgreSQL database.
It requires postgresql tool to be installed on your machine.

Depending on your OS, choose the relevant command to install postgresql:

AmazonLinux-CentOS
```bash
yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel python38-devel gcc unzip tar gzip
```

Ubuntu
```bash
apt-get install -yq libpq-dev postgresql postgresql-contrib
```

MacOS
```bash
brew install postgresql
```

**Install NPM packages**:
```bash
npm install -g aws-cdk
```

In addition, you will need at least two AWS account to which you have administrator credentials.

1. **Tooling account**: hosts the code repository, and the CI/CD pipeline.
2. **Deployment account**: hosts data.all backend and frontend AWS infrastructure.

If you are not deploying data.all in production mode, you could use the same AWS account as the Tooling and the Deployment account at the same time.

![Screenshot](assets/toolingdeployment.png#zoom#shadow)

!!!abstract "Multi-environment deployments"
    You can deploy data.all to multiple environments on the same or multiple AWS accounts (e.g DEV, QA, PROD) with approval steps by customizing the cdk.json file. 

!!!danger "Credentials for AWS Administrator"
    This guide assumes that you have **AWS Administrator credentials** ready to use on your terminal,
    to be able to run the different commands described below. Do not proceed if you are not administrator of the tooling
    account, and the deployment account(s).

## 1. Clone data.all code

Clone the GitHub repository from:
```bash
git clone https://github.com/awslabs/aws-dataall.git
cd aws-dataall
```
## 2. Install Python dependencies
Run the following commands:
```bash
pip install virtualenv
virtualenv venv -p python3.8
source venv/bin/activate
pip install git-remote-codecommit
make install
```

Assuming AWS tooling account Administrator credentials, create an AWS CodeCommit repository, mirror the data.all code 
and push your changes:

```bash
aws codecommit create-repository --repository-name dataall
git commit -m "First commit"
git remote add codecommit codecommit::<AWS_REGION>://dataall
git push codecommit main
```

## 3. Configure cdk.json
data.all gives you the ability to deploy the application infrastructure on multiple environments, with approval step when required (e.g production).

To customize deployment environments, update the blocks below with your relevant information like account number and environment name on **cdk.json** file:
````json
{
...
    "git_branch": "GIT_BRANCH_NAME",
    "tooling_vpc_id": "TOOLING_ACCOUNT_VPC_ID",
    "tooling_region": "TOOLING_ACCOUNT_REGION",
    "quality_gate": "TRUE_OR_FALSE",
    "DeploymentEnvironments": [
        {
            "envname": "ENVNAME_1",
            "account": "ACCOUNT_ID_1",
            "region": "REGION_1",
            "with_approval": false,
            "internet_facing": true,
            "enable_cw_rum": true,
            "enable_cw_canaries": true
        },
        {
            "envname": "ENVNAME_2",
            "account": "ACCOUNT_ID_2",
            "region": "REGION_2",
            "with_approval": true,
            "internet_facing": false,
            "vpc_id": "vpc-xxxxxxxxxxxxxx",
            "custom_domain": {
		      "domain_name":"ROUTE_53_DOMAIN_NAME",
		      "hosted_zone_id":"ROUTE_53_HOSTED_ZONE_ID"
		    },
            "ip_ranges": ["IP_RANGE1", "IP_RANGE2"],
            "apig_vpce": "vpce-xxxxxxxxxxxxxx"
        }
    ]
}
````

| Parameter             |Optional/Required| Definition
|-----------------------|---------|------------------------------------------------------------------------------------|
|tooling_vpc_id|Optional| The VPC ID for the **tooling** account. If not provided **a new VPC** will be created.          |
|tooling_region|Optional| The AWS region for the **tooling** account where the AWS CodePipeline pipeline will be created. if not provided **eu-west-1** will be used as default region.          |
|git_branch|Optional| The git branch name can be leveraged **to deploy multiple AWS CodePipeline pipelines to the same tooling account**. if not provided **main** will be used as default branch         |
|git_release|Optional| If set to **true**  an additional step on AWS CodePipeline to update data.all minor version and creates a git release tag for the deployed code.         |
|envname|Required| The name of the **deployment** environment (e.g dev, qa, prod)            |
|resource_prefix|Required| The prefix used for AWS created resources. default is data.all. As this field will be used to create resources, it must be in lower case without any special caracter          |
|account|Required| The AWS **deployment** account number          |
|region|Required| The AWS **deployment** region       |
|with_approval|Optional| If set to **true**  an additional step on AWS CodePipeline to require user approval before proceeding with the deployment.           |
|internet_facing|Optional|If set to **true**  CloudFront is used for hosting data.all UI and Docs and APIs are public. if false ECS is used to host static sites and APIs are private.  |
|vpc_id|Optional|The VPC ID for the **deployment** account. If not provided **a new VPC** will be created.|
|vpc_endpoints_sg|Optional| The VPC endpoints security groups to be use by AWS services to connect to VPC endpoints. if not assigned NAT outbound rule is used.     |
|custom_domain|Optional| If internet_facing parameter is **false** then custom_domain is mandatory for ECS ALB integration with ACM and HTTPS. It is not required when internet_facing is false, but it will be used for CloudFront if it's provided.
|ip_ranges|Optional| Used only when internet_facing parameter is **false**  to allow API Gateway resource policy to allow these IP ranges in addition to the VPC's CIDR block.
|apig_vpce|Optional| Used only when internet_facing parameter is **false** , if provided it will be used for API Gateway otherwise a new VPCE will be created.
|prod_sizing|Optional| If set to **true** infrastructure sizing is adapted to prod environments (default: true)      |
|quality_gate|Optional| If set to **true** CI/CD pipeline quality gate stage is enabled (default: true)      |
|enable_cw_rum|Optional|If set to **true** CloudWatch RUM monitor is created to monitor the user interface (default: false)      |
|enable_cw_canaries|Optional|If set to **true** CloudWatch Synthetics Canaries are created to monitor the GUI workflow of principle features (default: false)      |


## 4. Run CDK synth and configure cdk.context.json
Run `cdk synth` to create the template that will be later deployed to CloudFormation. 
With this command, CDK will create a **cdk.context.json** file that has different information retrieved from your AWS account.

Below an example of a generated cdk.context.json file:
````json
{
  "vpc-provider:account=012356789012:filter.vpc-id=vpc-882815d01cf2f70a1:region=eu-west-1:returnAsymmetricSubnets=true": {
    "vpcId": "vpc-882815d01cf2f70a1",
    "vpcCidrBlock": "10.116.112.0/22",
    "availabilityZones": [],
    "subnetGroups": [
      {
        "name": "Private",
        "type": "Private",
        "subnets": [
          {
            "subnetId": "subnet-05d8669ee34d05603",
            "cidr": "10.116.112.0/23",
            "availabilityZone": "eu-west-1a",
            "routeTableId": "rtb-0758ed8d32b56fbae"
          },
          {
            "subnetId": "subnet-038351a53eb1c3e58",
            "cidr": "10.116.114.0/24",
            "availabilityZone": "eu-west-1b",
            "routeTableId": "rtb-0758ed8d32b56fbae"
          },
          {
            "subnetId": "subnet-0d5115d3dbc87deda",
            "cidr": "10.116.115.0/24",
            "availabilityZone": "eu-west-1c",
            "routeTableId": "rtb-0758ed8d32b56fbae"
          }
        ]
      }
    ]
  }
}
````

## 5. Add CDK context file
The generated cdk.context.json file **must** be added to your source code and pushed into the previously created CodeCommit
repository running the commands below (remember, with the tooling account credentials):
```bash
git add cdk.json
git add cdk.context.json
git commit -m "CDK configuration"
git push codecommit main
```

## 6. Bootstrap the Tooling account
The **Tooling** account is where the code repository, and the CI/CD pipeline are deployed.
It needs to be bootstrapped with CDK in 2 regions, run the commands below with the AWS credentials of the tooling account:

**Your region (can be any supported region)**
```bash
cdk bootstrap aws://YOUR_TOOLING_ACCOUNT_ID/YOUR_REGION
```
**North Virginia region (needed to be able to deploy cross region to us-east-1)**
```bash
cdk bootstrap aws://YOUR_TOOLING_ACCOUNT_ID/us-east-1
```
## 7. Bootstrap the Deployment account(s)
The **Deployment** account is where the data.all application infrastructure will be deployed.
It needs to be bootstrapped with CDK in 2 regions, run the commands below with the AWS credentials of the deployment account:

Your region (can be any supported region)
```bash
cdk bootstrap --trust YOUR_TOOLING_ACCOUNT_ID -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://YOUR_DEPLOYMENT_ACCOUNT_ID/YOUR_REGION
```
North Virginia region (needed for Cloudfront integration with ACM on us-east-1)
```bash
cdk bootstrap --trust YOUR_TOOLING_ACCOUNT_ID -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://YOUR_DEPLOYMENT_ACCOUNT_ID/us-east-1
```
!!!danger "Multiple deployment accounts"
    When specifying multiple deployment accounts on cdk.json file, **all** these accounts
      need to be bootstrapped on your region and us-east-1.


## 8. Run CDK deploy
You are all set to start the deployment, run the command below:
```bash
cdk deploy {resource_prefix}-{git_branch}-cicd-stack
```
Replace the `resource_prefix` and `git_branch` by their values in the cdk.json file.

## **Additional resources**

**How does the `prod_sizing` field in `cdk.json` affect the architecture ?**

This field defines the size of the backend resource. It is recommended to set it to `true` when deploying into a production environment, and `false` otherwise.
By setting the value to `true`, data.all backend resources are more available and scale faster.
When setting the value to `false`, backend resources become smaller but you save up on cost.

These are the resources affected:

| Backend Service |prod_sizing| Configuration
|----|----|----|
|Aurora |true| - Deletion protection enabled <br /> - Backup retention of 30 days <br /> - Paused after 1 day of inactivity <br /> - Max capacity unit of 16 ACU <br /> - Min capacity unit of 4 ACU |
|Aurora |false| - Deletion protection disabled <br /> - No backup retention <br /> - Paused after 10 mintes of inactivity <br /> - Max capacity unit of 8 ACU <br /> - Min capacity unit of 2 ACU |
|OpenSearch |true| - The KMS key of the OpenSearch cluster is kept when the CloudFormation stack is deleted <br /> - Cluster configured with 3 master node and 2 data nodes <br /> - Each data node has an EBS volume of 30GiB attached to it |
|OpenSearch |false| - The KMS key of the OpenSearch cluster gets deleted when the CloudFormation stack is deleted <br /> - Cluster configured with 0 master node and 2 data nodes <br /> - Each data node has an EBS volume of 20GiB attached to it |
|Lambda function |true| - Lambda functions are configured with more memory|
|Lambda function |false| - Lambda functions are configured with less memory|
