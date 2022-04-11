---
layout: default_sublevel
title: Deploy to AWS
permalink: /deploy-aws/
---

# **Getting Started**
You can deploy data.all in your AWS accounts by following the steps in the "Deploy to AWS" section. If you are a developer
and want to have a look and run the code locally check out the "Deploy locally" section.

## Pre-requisites
You need to have the tools below up and running to proceed with the deployment:

* python 3.8
* virtualenv `pip install virtualenv`
* node
* npm
* aws-cdk: installed globally `npm install -g aws-cdk`
* aws-cdk credentials plugin: installed globally `npm install -g cdk-assume-role-credential-plugin`
* aws-cli (v2)
* git client




In addition, you will need at least two AWS accounts. For each of these accounts you will need **AWS Administrator credentials** 
ready to use on your terminal. Do not proceed if you are not administrator in the tooling
account, and in the deployment account(s).

1. **Tooling account**: hosts the code repository, and the CI/CD pipeline.
2. **Deployment account(s)**: hosts data.all's backend, and frontend AWS infrastructure. You can deploy 
data.all to multiple environments on the same or multiple AWS accounts (e.g DEV, TEST, QA, PROD). 

**Note**: If you are not deploying data.all in production mode, you could use the same AWS account as the Tooling 
and the Deployment account.


![Screenshot](pages/img/architecture_tooling.drawio.png#zoom#shadow)


## 1. Setup Python virtualenv
From your personal computer or from Cloud9 in the AWS Console, create a python virtual environment from the code using python 3.8, then add CodeCommit git plugin with the following commands:

```bash
virtualenv venv -p python3.8
source venv/bin/activate
pip install git-remote-codecommit
```

Then, install Python requirements:
```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install -r backend/data.all/cdkproxy/requirements.txt
```
## 2. Clone data.all code

Clone the GitHub repository from:
```bash
git clone https://github.com/awslabs/aws-dataall.git
cd aws-dataall
```
Assuming AWS tooling account Administrator credentials, create an AWS CodeCommit repository, mirror the data.all code 
and push your changes:

```bash
aws codecommit create-repository --repository-name aws-dataall
git init
git add .
git commit -m "First commit"
git remote add origin codecommit::<AWS_REGION>://aws-dataall
git push origin main
```

## 3. Configure cdk.json
To configure and customize your deployment environments, update the parameters of the **cdk.json** file. Check the 
table below with the list and description of optional and mandatory parameters.

**Note**: by specifying multiple environment blocks, like in the example "DEV" and "PROD", data.all will
deploy to 2 deployments accounts with a CodePipeline manual approval stage between them. 


````json
{
...
    "git_branch": "main",
    "tooling_vpc_id": "vpc-1234567890EXAMPLE",
    "tooling_region": "eu-weast-1",
    "quality_gate": "TRUE",
    "DeploymentEnvironments": [
        {
            "envname": "DEV",
            "account": "000000000000",
            "region": "eu-weast-1",
            "with_approval": false,
            "internet_facing": true,
            "enable_cw_rum": true,
            "enable_cw_canaries": true
        },
        {
            "envname": "PROD",
            "account": "111111111111",
            "region": "eu-weast-1",
            "with_approval": true,
            "internet_facing": false,
            "vpc_id": "vpc-0987654321EXAMPLE",
            "cf_alternate_domain_config": {
		      "data.all_custom_domain":"example.com",
		      "data.all_domain_hosted_zone_id":"ROUTE_53_HOSTED_ZONE_ID"
		    },
            "ip_ranges": ["IP_RANGE1", "IP_RANGE2"],
            "apig_vpce": "vpc-xxxxxxxxxxxxxx"
        }
    ]
}
````

| Parameter             |Optional/Required| Definition                                                                                                                                                                                                                                
|-----------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|tooling_vpc_id|Optional| The VPC ID for the **tooling** account. If not provided, **a new VPC** will be created.                                                                                                                                                   |
|tooling_region|Optional| The AWS region for the **tooling** account where the AWS CodePipeline pipeline will be created. If not provided, **eu-west-1** will be used as default region.                                                                            |
|git_branch|Optional| The git branch name can be leveraged **to deploy multiple AWS CodePipeline pipelines** to the same tooling account. If not provided, **main** will be used as default branch.                                                             |
|envname|Required| The name of the deployment environment (e.g dev, qa, prod,...)                                                                                                                                                                            |
|resource_prefix|Required| The prefix used for AWS created resources. Default is dataall. It must be in lower case without any special character.                                                                                                                    |
|account|Required| The AWS deployment account (deployment account N)                                                                                                                                                                                         |
|region|Required| The AWS deployment region                                                                                                                                                                                                                 |
|with_approval|Optional| If set to **true**  an additional step on AWS CodePipeline to require user approval before proceeding with the deployment.                                                                                                                |
|internet_facing|Optional| If set to **true**  CloudFront is used for hosting data.all UI and Docs and APIs are public. If false, ECS is used to host static sites and APIs are private.                                                                             |
|vpc_id|Optional| The VPC ID for the **deployment** account. If not provided, **a new VPC** will be created.                                                                                                                                                |
|vpc_endpoints_sg|Optional| The VPC endpoints security groups to be use by AWS services to connect to VPC endpoints. If not assigned, NAT outbound rule is used.                                                                                                      |
|cf_alternate_domain_config|Optional| If internet_facing parameter is **false** then cf_alternate_domain_config is mandatory for ECS ALB integration with ACM and HTTPS. It is not required when internet_facing is false, but it will be used for CloudFront if it's provided. 
|ip_ranges|Optional| Used only when internet_facing parameter is **false**  to allow API Gateway resource policy to allow these IP ranges in addition to the VPC's CIDR block.                                                                                 
|apig_vpce|Optional| Used only when internet_facing parameter is **false**. If provided, it will be used for API Gateway otherwise a new VPCE will be created.                                                                                                 
|prod_sizing|Optional| If set to **true**, infrastructure sizing is adapted to prod environments (default: true). Check additional resources section for more details.                                                                                           |
|quality_gate|Optional| If set to **true**, CI/CD pipeline quality gate stage is enabled (default: true)                                                                                                                                                          |
|enable_cw_rum|Optional| If set to **true** CloudWatch RUM monitor is created to monitor the user interface (default: false)                                                                                                                                       |
|enable_cw_canaries|Optional| If set to **true**, CloudWatch Synthetics Canaries are created to monitor the GUI workflow of principle features (default: false)                                                                                                         |


## 4. Run CDK synth and configure cdk.context.json
Run `cdk synth` to create the template that will be later deployed to CloudFormation. 
With this command, CDK will create a **cdk.context.json** file that has different information retrieved from your AWS account.

Below an example of a generated cdk.context.json file:
````json
{
  "vpc-provider:account=XXX:filter.vpc-id=vpc-XXX:region=eu-west-1:returnAsymmetricSubnets=true": {
    "vpcId": "vpc-1234567890EXAMPLE",
    "vpcCidrBlock": "xxx.xxx.xxx.xxx/22",
    "availabilityZones": [],
    "subnetGroups": [
      {
        "name": "Private",
        "type": "Private",
        "subnets": [
          {
            "subnetId": "subnet-XXX",
            "cidr": "xxx.xxx.xxx.xxx/23",
            "availabilityZone": "eu-west-1a",
            "routeTableId": "rtb-XXX"
          },
          {
            "subnetId": "subnet-XXX",
            "cidr": "xxx.xxx.xxx.xxx/24",
            "availabilityZone": "eu-west-1b",
            "routeTableId": "rtb-XXX"
          },
          {
            "subnetId": "subnet-XXX",
            "cidr": "xxx.xxx.xxx.xxx/24",
            "availabilityZone": "eu-west-1c",
            "routeTableId": "rtb-XXX"
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
git push
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
The **Deployment** account(s) is where the data.all application infrastructure will be deployed.
Each of the deployment account(s) needs to be bootstrapped with CDK in 2 regions, run the commands below with the AWS credentials of the deployment account:

Your region (can be any supported region)
```bash
cdk bootstrap --trust YOUR_TOOLING_ACCOUNT_ID -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://YOUR_DEPLOYMENT_ACCOUNT_ID/YOUR_REGION
```
North Virginia region (needed for Cloudfront integration with ACM on us-east-1)
```bash
cdk bootstrap --trust YOUR_TOOLING_ACCOUNT_ID -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://YOUR_DEPLOYMENT_ACCOUNT_ID/us-east
```


## 8. Run CDK deploy
You are all set to start the deployment, run the command below. 
Replace the `resource_prefix` and `git_branch` by their values in the cdk.json file.

```bash
cdk deploy {resource_prefix}-{git_branch}-cicd-stack
```


## 9. Configure Cloudwatch RUM

1. Open AWS Console
2. Go to CloudWatch service on the left panel under Application monitoring open RUM
3. Select your environment (data.all-envname-monitor) and click on edit button like the figure below:
![Screenshot](pages/assets/rum_list.png#zoom#shadow)
4. Update the domain with your Route53 domain name or your CloudFront distribution domain (omit https://), and check include subdomains.
![Screenshot](pages/assets/rum_update.png#zoom#shadow)
5. Copy to clipboard the javascript code suggested on the console.
![Screenshot](pages/assets/rum_clipboard.png#zoom#shadow)
6. Open data.all codebase on an IDE and open the file `data.all/frontend/public/index.html`
7. Paste the code on the clipboard like below:
![Screenshot](pages/assets/rum_code_update.png#zoom#shadow)
8. Commit and push your changes.


## 🎉 Congratulations 🎉
You've successfully deployed data.all on your AWS accounts! Check out the User Guide to start working on your data 
marketplace or the other sections of this guide, Architecture/Code/Security, to develop your platform further.

## Additional resources

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




