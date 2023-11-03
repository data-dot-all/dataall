---
layout: default_sublevel
title: Deploy to AWS
permalink: /deploy-aws/
---

# **Getting Started: Deploy to AWS**
You can deploy data.all in your AWS accounts by following these steps:

## Pre-requisites
You need to have the tools below up and running to proceed with the deployment:

* python 3.8 or higher
* virtualenv `pip install virtualenv`
* node
* npm
* aws-cdk: installed globally `npm install -g aws-cdk`
* aws-cdk credentials plugin: installed globally `npm install -g cdk-assume-role-credential-plugin`
* aws-cli (v2)
* git client

Run the below command to verify that you have git cli installed. It should list your `user.name` and `user.email` at a minimum.
```bash
git config --list
```


In addition, you will need at least two AWS accounts. For each of these accounts you will need **AWS Administrator credentials** 
ready to use on your terminal. Do not proceed if you are not administrator in the tooling
account, and in the deployment account(s).

- **Tooling account**: hosts the code repository, and the CI/CD pipeline. We can use any region to deploy the CI/CD resources
if the underlying AWS services (CodeCommit, CodeBuild...) are available in the selected region. In addition, you will need
access to a second region. The reason is that we use [CDK Pipelines](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html), 
an opinionated CDK construct that deploys a cross-region replication support stack. For all regions except `us-east-1` the replication region is `us-east-1`.
- **Deployment account(s)**: hosts data.all's backend and frontend AWS infrastructure. You can deploy 
data.all to multiple environments on the same or multiple AWS accounts (e.g dev, test, qa, prod). If deployment is configured
with `internet_facing` set to true, `us-east-1` is required for the deployment of some frontend components. 
Backend resources can be hosted in any region given that the AWS services used are available.

**Note**: If you are not deploying data.all in production mode, you could use the same AWS account as the Tooling 
and the Deployment account.

Make sure that the AWS services used in data.all are available in the Regions you choose for tooling and deployment. 
Check out the [Architecture](../architecture/). Moreover, data.all uses [CDK Pipelines](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.pipelines-readme.html) in the Tooling account,
which means that AWS services used by this construct need to be available in the tooling account (e.g. CodeArtifact).

## 1. Clone data.all code

Clone the GitHub repository from:
```bash
git clone https://github.com/awslabs/aws-dataall.git
cd aws-dataall
```
## 2. Setup Python virtualenv
From your personal computer or from Cloud9 in the AWS Console, create a python virtual environment 
from the code using python 3.8, then install the necessary deploy requirements with the following commands:

```bash
virtualenv venv
source venv/bin/activate
pip install -r ./deploy/requirements.txt
pip install git-remote-codecommit
```

## 3. Mirror the code to a CodeCommit repository
Assuming AWS tooling account Administrator credentials, create an AWS CodeCommit repository, mirror the data.all code 
and push your changes:
Run the following to check your credentials:
```bash
aws sts get-caller-identity
```
```bash
aws codecommit create-repository --repository-name dataall
git remote rm origin
git remote add origin codecommit::<aws-region>://dataall
git init
git add .
git commit -m "First commit"
git push --set-upstream origin main
```
## 4. Bootstrap tooling account
The **Tooling** account is where the code repository, and the CI/CD pipeline are deployed.
It needs to be bootstrapped with CDK in 2 regions, your selected region and us-east-1.

The **Deployment** account(s) is where the data.all application infrastructure will be deployed.
Each of the deployment account(s) needs to be bootstrapped with CDK in 2 regions, your selected region and us-east-1.


Run the commands below with the AWS credentials of the tooling account:

Your region (can be any supported region)
```bash
cdk bootstrap aws://<tooling-account-id>/<aws-region>
```
North Virginia region (needed to be able to deploy cross region to us-east-1)
```bash
cdk bootstrap aws://<tooling-account-id>/us-east-1
```
## 5. Bootstrap deployment account(s)

Run the commands below with the AWS credentials of the deployment account:

Your region (can be any supported region)
```bash
cdk bootstrap --trust <tooling-account-id> --trust-for-lookup <tooling-account-id> -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://<deployment-account-id>/<aws-region>
```

If you plan to configure the deployment with internet-facing frontend, you also need to bootstrap the North Virginia region (needed for Cloudfront integration with ACM on us-east-1)
```bash
cdk bootstrap --trust <tooling-account-id> --trust-for-lookup <tooling-account-id> -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://<deployment-account-id>/us-east-1
```


## 6. Configure the deployment options in the cdk.json file
We use a parameters cdk.json file to configure and customize your deployment of data.all. This file is at the root level
of our repository. Open it, you should be seen something like:
```json
{
  "app": "python ./deploy/app.py",
  "context": {
    "@aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId": false,
    "@aws-cdk/aws-cloudfront:defaultSecurityPolicyTLSv1.2_2021": true,
    "@aws-cdk/aws-rds:lowercaseDbIdentifier": false,
    "@aws-cdk/core:stackRelativeExports": false,
    "tooling_region": "string_TOOLING_REGION|DEFAULT=eu-west-1",
    "tooling_vpc_id": "string_IMPORT_AN_EXISTING_VPC_FROM_TOOLING|DEFAULT=None",
    "tooling_vpc_restricted_nacl": "boolean_CREATE_CUSTOM_NACL|DEFAULT=false",
    "git_branch": "string_GIT_BRANCH_NAME|DEFAULT=dataall",
    "git_release": "boolean_MANAGE_GIT_RELEASE|DEFAULT=false",
    "quality_gate": "boolean_MANAGE_QUALITY_GATE_STAGE|DEFAULT=true",
    "resource_prefix": "string_PREFIX_FOR_ALL_RESOURCES_CREATED_BY_THIS_APP|DEFAULT=dataall",
    "DeploymentEnvironments": [
      {
        "envname": "string_ENVIRONMENT_NAME|REQUIRED",
        "account": "string_DEPLOYMENT_ACCOUNT|REQUIRED",
        "region": "string_DEPLOYMENT_REGION|REQUIRED",
        "with_approval": "boolean_ADD_CODEPIPELINE_APPROVAL_STEP|DEFAULT=false",
        "vpc_id": "string_DEPLOY_WITHIN_AN_EXISTING_VPC|DEFAULT=None",
        "vpc_endpoints_sg": "string_DEPLOY_WITHIN_EXISTING_VPC_SG|DEFAULT=None",
        "vpc_restricted_nacl": "boolean_CREATE_CUSTOM_NACL|DEFAULT=false",
        "internet_facing": "boolean_CLOUDFRONT_IF_TRUE_ELSE_ECS_BEHIND_INTERNAL_ALB|DEFAULT=true",
        "custom_domain": {
          "hosted_zone_name": "string_ROUTE_53_EXISTING_DOMAIN_NAME|DEFAULT=None, REQUIRED if internet_facing=false",
          "hosted_zone_id": "string_ROUTE_53_EXISTING_HOSTED_ZONE_ID|DEFAULT=None",
          "certificate_arn": "string_AWS_CERTIFICATE_MANAGER_EXISTING_CERTIFICATE_ARN|DEFAULT=None, REQUIRED if internet_facing=false"
          "email_notification_sender_email_id":"string_EMAIL_NOTIFICATION_SENDER_EMAIL_ID|DEFAULT=None"
        },
        "ip_ranges": "list_of_strings_IP_RANGES_TO_ALLOW_IF_NOT_INTERNET_FACING|DEFAULT=None",
        "apig_vpce": "string_USE_AN_EXISTING_VPCE_FOR_APIG_IF_NOT_INTERNET_FACING|DEFAULT=None",
        "prod_sizing": "boolean_SET_INFRA_SIZING_TO_PROD_VALUES_IF_TRUE|DEFAULT=true",
        "enable_cw_rum":  "boolean_SET_CLOUDWATCH_RUM_APP_MONITOR|DEFAULT=false",
        "enable_cw_canaries": "boolean_SET_CLOUDWATCH_CANARIES_FOR_FRONTEND_TESTING|DEFAULT=false",
        "enable_quicksight_monitoring": "boolean_ENABLE_CONNECTION_QUICKSIGHT_RDS|DEFAULT=false",
        "shared_dashboards_sessions": "string_TYPE_SESSION_SHARED_DASHBOARDS|(reader, anonymous) DEFAULT=anonymous",
        "enable_pivot_role_auto_create": "boolean_ENABLE_PIVOT_ROLE_AUTO_CREATE_IN_ENVIRONMENT|DEFAULT=false",
        "enable_update_dataall_stacks_in_cicd_pipeline": "boolean_ENABLE_UPDATE_DATAALL_STACKS_IN_CICD_PIPELINE|DEFAULT=false",
        "enable_opensearch_serverless": "boolean_USE_OPENSEARCH_SERVERLESS|DEFAULT=false",
        "cognito_user_session_timeout_inmins": "integer_COGNITO_USER_SESSION_TIMEOUT_INMINS|DEFAULT=43200",
        "reauth_config": {
          "reauth_apis": "list_of_strings_OPERATION_NAMES_TO_REQUIRE_REAUTH_ON|DEFAULT=None",
          "ttl": "int_TIME_IN_MINUTES_TO_ALLOW_USER_TO_PERFORM_SENSITIVE_APIS_BEFORE_FORCING_REAUTH|DEFAULT=5"
        }
      }
    ]
  }
}
```
Some parameters are required while others are optional. Below, we
have listed and defined all the parameters of the cdk.json file. If you still have questions, scroll down 
and find 2 examples of cdk.json files.


| **General Parameters**                        | **Optional/Required** | **Definition**                                                                                                                                                                                                                                                                                                                                              |   
|-----------------------------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| tooling_vpc_id                                | Optional              | The VPC ID for the tooling account. If not provided, **a new VPC** will be created.                                                                                                                                                                                                                                                                         |
| tooling_region                                | Optional              | The AWS region for the tooling account where the AWS CodePipeline pipeline will be created. (default: eu-west-1)                                                                                                                                                                                                                                            |
| tooling_vpc_restricted_nacl                   | Optional              | If set to **true**, VPC NACLs added to restrict network traffic on the subnets of the data.all provisioned tooling VPC (default: false)                                                                                                                                                                                                                     |
| git_branch                                    | Optional              | The git branch name can be leveraged to deploy multiple AWS CodePipeline pipelines to the same tooling account. (default: main)                                                                                                                                                                                                                             |
| git_release                                   | Optional              | If set to **true**, CI/CD pipeline RELEASE stage is enabled. This stage releases a version out of the current branch. (default: false)                                                                                                                                                                                                                      |
| quality_gate                                  | Optional              | If set to **true**, CI/CD pipeline quality gate stage is enabled. (default: true)                                                                                                                                                                                                                                                                           |
| resource_prefix                               | Optional              | The prefix used for AWS created resources. It must be in lower case without any special character. (default: dataall)                                                                                                                                                                                                                                       |
| **Deployment environments Parameters**        | **Optional/Required** | **Definition**                                                                                                                                                                                                                                                                                                                                              |
| ----------------------------                  | ---------             | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------                                                                                                                 |
| envname                                       | REQUIRED              | The name of the deployment environment (e.g dev, qa, prod,...). It must be in lower case without any special character.                                                                                                                                                                                                                                     |
| account                                       | REQUIRED              | The AWS deployment account (deployment account N)                                                                                                                                                                                                                                                                                                           |
| region                                        | REQUIRED              | The AWS deployment region                                                                                                                                                                                                                                                                                                                                   |
| with_approval                                 | Optional              | If set to **true**  an additional step on AWS CodePipeline to require user approval before proceeding with the deployment. (default: false)                                                                                                                                                                                                                 |
| vpc_id                                        | Optional              | The VPC ID for the deployment account. If not provided, **a new VPC** will be created.                                                                                                                                                                                                                                                                      |
| vpc_endpoints_sg                              | Optional              | The VPC endpoints security groups to be use by AWS services to connect to VPC endpoints. If not assigned, NAT outbound rule is used.                                                                                                                                                                                                                        |
| vpc_restricted_nacl                           | Optional              | If set to **true**, VPC NACLs added to restrict network traffic on the subnets of the data.all provisioned deployment VPC (default: false)                                                                                                                                                                                                                  |
| internet_facing                               | Optional              | If set to **true**  CloudFront is used for hosting data.all UI and Docs and APIs are public. If false, ECS is used to host static sites and APIs are private. (default: true)                                                                                                                                                                               |
| custom_domain                                 | Optional*             | Custom domain configuration: `hosted_zone_name`, `hosted_zone_id`, `certificate_arn`, and `email_notification_sender_email_id`. If internet_facing parameter is **false** or `share_notifications.email` is active in `config.json` then custom_domain is REQUIRED for ECS ALB integration with ACM and HTTPS. It is optional when internet_facing is true. |
| ip_ranges                                     | Optional              | Used only when internet_facing parameter is **false**  to allow API Gateway resource policy to allow these IP ranges in addition to the VPC's CIDR block.                                                                                                                                                                                                   |
| apig_vpce                                     | Optional              | Used only when internet_facing parameter is **false**. If provided, it will be used for API Gateway otherwise a new VPCE will be created.                                                                                                                                                                                                                   |
| prod_sizing                                   | Optional              | If set to **true**, infrastructure sizing is adapted to prod environments. Check additional resources section for more details.  (default: true)                                                                                                                                                                                                            |
| enable_cw_rum                                 | Optional              | If set to **true** CloudWatch RUM monitor is created to monitor the user interface (default: false)                                                                                                                                                                                                                                                         |
| enable_cw_canaries                            | Optional              | If set to **true**, CloudWatch Synthetics Canaries are created to monitor the GUI workflow of principle features (default: false)                                                                                                                                                                                                                           |
| enable_quicksight_monitoring                  | Optional              | If set to **true**, RDS security groups and VPC NACL rules are modified to allow connection of the RDS metadata database with Quicksight in the infrastructure account (default: false)                                                                                                                                                                     |
| shared_dashboard_sessions                     | Optional              | Either 'anonymous' or 'reader'. It indicates the type of Quicksight session used for Shared Dashboards (default: 'anonymous')                                                                                                                                                                                                                               |
| enable_pivot_role_auto_create                 | Optional              | If set to **true**, data.all creates the pivot IAM role as part of the environment stack. If false, a CloudFormation template is provided in the UI and AWS account admins need to deploy this stack as pre-requisite to link a data.all environment (default: false)                                                                                       |
| enable_update_dataall_stacks_in_cicd_pipeline | Optional              | If set to **true**, CI/CD pipeline update stacks stage is enabled for the deployment environment. This stage triggers the update of all environment and dataset stacks (default: false)                                                                                                                                                                     |
| enable_opensearch_serverless                  | Optional              | If set to **true** Amazon OpenSearch Serverless collection is created and used instead of Amazon OpenSearch Service domain (default: false)                                                                                                                                                                                                                 |
| cognito_user_session_timeout_inmins           | Optional              | The number of minutes to set the refresh token validity time for user session's in Cognito before a user must re-login to the data.all UI (default: 43200 - i.e. 30 days)                                                                                                                                                                                   |
| reauth_config                                 | Optional              | A dictionary containing a list of API operations that require a user to re-authenticate before proceedind (`reauth_apis`) and a time to live (`ttl`) for how long a user's re-auth session is valid to perform re-auth APIs before having to re-authenticate again                                                                                          |

**Example 1**: Basic deployment: this is an example of a minimum configured cdk.json file.

```json
{
  "app": "python ./deploy/app.py",
  "context": {
    "@aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId": false,
    "@aws-cdk/aws-cloudfront:defaultSecurityPolicyTLSv1.2_2021": true,
    "@aws-cdk/aws-rds:lowercaseDbIdentifier": false,
    "@aws-cdk/core:stackRelativeExports": false,
    "DeploymentEnvironments": [
        {
            "envname": "sandbox",
            "account": "000000000000",
            "region": "eu-west-1"
        }
    ]
  }
}
```

**Example 2**: Customized deployment: here we are customizing the cdk.json with all 
parameters using their non-default values in at least one of the 
deployments. By specifying multiple environment blocks, "dev" and "prod", data.all will
deploy to 2 deployments accounts. 

```json
{
  "app": "python ./deploy/app.py",
  "context": {
    "@aws-cdk/aws-apigateway:usagePlanKeyOrderInsensitiveId": false,
    "@aws-cdk/aws-cloudfront:defaultSecurityPolicyTLSv1.2_2021": true,
    "@aws-cdk/aws-rds:lowercaseDbIdentifier": false,
    "@aws-cdk/core:stackRelativeExports": false,
    "tooling_vpc_id": "vpc-1234567890EXAMPLE",
    "tooling_region": "eu-west-2",
    "tooling_vpc_restricted_nacl": true,
    "git_branch": "master",
    "git_release": true,
    "quality_gate": false,
    "resource_prefix": "da",
    "DeploymentEnvironments": [
        {
            "envname": "dev",
            "account": "000000000000",
            "region": "eu-west-1",
            "with_approval": false,
            "internet_facing": true,
            "prod_sizing": false,
            "enable_cw_rum": true,
            "enable_cw_canaries": true
          
        },
        {
            "envname": "prod",
            "account": "111111111111",
            "region": "eu-west-1",
            "with_approval": true,
            "internet_facing": false,
            "vpc_id": "vpc-0987654321EXAMPLE",
            "vpc_endpoints_sg": "sg-xxxxxxxxxxxxxx",
            "vpc_restricted_nacl": true,
            "custom_domain": {
              "hosted_zone_name":"example.com",
              "hosted_zone_id":"ROUTE_53_HOSTED_ZONE_ID",
              "certificate_arn":"arn:aws:acm:AWS_REGION:AWS_ACCOUNT_ID:certificate/CERTIFICATE_ID"
            },
            "ip_ranges": ["IP_RANGE1", "IP_RANGE2"],
            "apig_vpce": "vpc-xxxxxxxxxxxxxx",
            "enable_pivot_role_auto_create": true,
            "enable_update_dataall_stacks_in_cicd_pipeline": true,
            "enable_opensearch_serverless": true,
            "cognito_user_session_timeout_inmins": 240,
            "reauth_config": {
              "reauth_apis": ["CreateDataset", "ImportDataset", "deleteDataset"],
              "ttl": 10
            }
        }
    ]
  }
}
```
## 7. Configure the application modules in the config.json file
In data.all V2 you can enable, disable, configure and add new modules to your data.all deployment in the `config.json` file
located at the top level of the repository. Here is an example file, where you
can distinguish 2 parts: `modules` and `core`. Read the following subsections to understand each of these parts and 
the different configuration options. 

```json
{
    "modules": {
        "datasets": {
            "active": true,
            "features": {
                "file_uploads": false,
                "file_actions": true,
                "aws_actions": true,
                "preview_data": true,
                "glue_crawler": true,
                "share_notifications": {
                    "email": {
                        "active": false,
                        "parameters": {
                            "group_notifications": true
                        }
                    }
                },
            },
        },
        "mlstudio": {
            "active": true
        },
        "notebooks": {
            "active": true
        },
        "datapipelines": {
            "active": true
        },
        "worksheets": {
            "active": true
        },
        "dashboards": {
            "active": true
        }
    },
    "core": {
        "features": {
            "env_aws_actions": true
        }
    }
}
```

### Enable/disable modules
The first thing that you'll need to do is to set a certain module to `"active": true` to enable the module or `"active": false` to disable it. 
If a module is disabled, the module related APIs and frontend views won't be created.

If a module depends on other modules we do not need to explicitly define it as active in the `config.json`. For example,
`datasets` depend on the `dataset-sharing` module. `dataset-sharing` will be loaded even if we do not declare it in the
`config.json`.

The following table contains a list of the available modules and their dependencies with a very brief explanation of the
functionality. If you want to know more about each module, 
check the [UserGuide](https://github.com/awslabs/aws-dataall/blob/main/UserGuide.pdf) available as PDF in the repository.

| **Module**      | **depends on**                                      | **Description**                                                                       |   
|-----------------|-----------------------------------------------------|---------------------------------------------------------------------------------------|
| catalog         | None                                                | Central catalog of data items. In this module a glossary of terms is defined.         |
| feed            | None                                                | S3 Bucket and Glue database construct to store data in data.all                       |
| vote            | catalog                                             | S3 Bucket and Glue database construct to store data in data.all                       |
| datasets        | datasets_base, dataset_sharing, catalog, vote, feed | S3 Bucket and Glue database construct to store data in data.all                       |
| dataset_sharing | datasets_base, notifications                        | Sub-module that allows sharing of Datasets through Lake Formation and S3              |
| datasets_base   | None                                                | Shared code related to Datasets.                                                      |
| worksheets      | datasets                                            | Athena query editor integrated in data.all UI                                         |
| datapipelines   | feed                                                | CICD pipelines that deploy [AWS DDK](https://awslabs.github.io/aws-ddk/) applications |
| mlstudio        | None                                                | SageMaker Studio users that can open a session directly from data.all UI              |
| notebooks       | None                                                | SageMaker Notebooks created and accessible from data.all UI                           |
| dashboards      | catalog, vote, feed                                 | Start a Quicksight session or import and share a Quicksight Dashboard.                |
| notifications   | None                                                | Construct to notify users on dataset sharing updates in data.all                      |


### Disable module features
As you probably noticed, the `dataset` module contains an additional field called `features` in the `config.json`. 
If there is a particular functionality that you want to enable or disable you can do so in this section. 
In the example config.json, the feature that enables file upload from data.all UI has been disabled.

```json
    "datasets": {
        "active": true,
        "features": {
            "file_uploads": false,
            "file_actions": true,
            "aws_actions": true,
            "preview_data": true,
            "glue_crawler": true,
            "share_notifications": {
                "email": {
                    "active": false,
                    "parameters": {
                        "group_notifications": true
                    }
                }
            },
        }
    },
```
| **Feature**       | **Module** | **Description**                                                                                    |   
|-------------------|------------|----------------------------------------------------------------------------------------------------|
| file_uploads      | datasets   | Upload files in a Dataset in the Upload tab                                                        |
| file_actions      | datasets   | Create, Read, Update, Delete on Dataset Folders                                                    |
| aws_actions       | datasets   | Get AWS Credentials and assume Dataset IAM role from data.all's UI                                 |
| preview_data      | datasets   | Enable previews of dataset tables for users in data.all UI                                         |
| glue_crawler      | datasets   | Allow running Glue Crawler to catalog new data for data.all datasets directly from the UI          |
| share_notifications      | datasets   | Allow additional notifications (on top of data.all's built in UI notifications) to be sent to data.all users when a dataset sharing operation occurs (currently only type `email` notifications is supported and requires `custom_domain` hosted zone parameters be specified in `cdk.json`)         |

### Disable core features
In some cases, customers need to disable features that belong to the core functionalities of data.all. One way to restrict 
a particular feature in the core is to add it to the core section of the `config.json` and enable/disable it. 

```json
    "core": {
        "features": {
            "env_aws_actions": true
        }
    }
```
This is the list of core features that can be switched on/off at the moment. Take it as an example if you need to 
disable any other core feature.

| **Feature**           | **Module**     | **Description**                                                                  |   
|-----------------------|----------------|----------------------------------------------------------------------------------|
| env_aws_actions       | environments   | Get AWS Credentials and assume Environment Group IAM roles from data.all's UI    |



## 8. Run CDK synth and check cdk.context.json
Run `cdk synth` to create the template that will be later deployed to CloudFormation. 
With this command, CDK will create a **cdk.context.json** file with key-value pairs that are checked at 
synthesis time. Think of them as environment variables for the synthesis of CloudFormation stacks. 
`cdk synth` retrieves information from the AWS account that the AWS CLI has access to. For this reason
we will run `cdk synth` as many times as AWS accounts we are using, with the corresponding credentials:

- With tooling account AWS credentials:
```bash
cdk synth
```
- With deployment account N AWS credentials:
```bash
cdk synth
```
Here is an example of a generated cdk.context.json file:
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

## 9. Add CDK context file
The generated cdk.context.json file **must** be added to your source code and pushed into the previously created CodeCommit
repository. Add the generated context file to the repo by running the commands below 
(remember, with the tooling account credentials).
```bash
git add cdk.json
git add cdk.context.json
git commit -m "CDK configuration"
git push
```

## 10. Run CDK deploy
You are all set to start the deployment, with the AWS credentials for the tooling account, run the command below. 
Replace the `resource_prefix` and `git_branch` by their values in the cdk.json file. 

```bash
cdk deploy <resource_prefix>-<git_branch>-cicd-stack
```
In case you used the default values, this is how the command would look like:
```bash
cdk deploy dataall-main-cicd-stack
```
## 11. Configure Cloudwatch RUM (enable_cw_rum=true)

If you enabled CloudWatch RUM in the **cdk.json** file: 

1. Open AWS Console
2. Go to CloudWatch service on the left panel under Application monitoring open RUM
3. Select your environment (data.all-envname-monitor) and click on edit button.
4. Update the domain with your Route53 domain name or your CloudFront distribution domain (omit https://), and check include subdomains.
5. Copy to clipboard the javascript code suggested on the console.
![Screenshot](../img/rum_clipboard.png#zoom#shadow)
6. Open data.all codebase on an IDE and open the file `data.all/frontend/public/index.html`
7. Paste the code on the clipboard like below:
![Screenshot](../img/rum_code_update.png#zoom#shadow)
8. Commit and push your changes.


## 🎉 Congratulations - What I have just done? 🎉
You've successfully deployed data.all CI/CD to your tooling account, namely, the resources that you see in the
diagram.

![archi](../img/architecture_tooling.drawio.png#zoom#shadow)

With this pipeline we can now deploy the infrastructure to the deployment account(s). Navigate to AWS CodePipeline
in the tooling account and check the status of your pipeline.

## 12. Setting SES for Email Notifications

Please follow instructions from below only if you have enabled email notifications on share workflow by switching the email.active config ( from `config.json` file ) to `true` in the `share_notifications` feature under `datasets` module.

### Moving AWS SES out of Sandbox
If you have specified `custom_domain`, after the deployment you should see a SES identity which is formed in your AWS Account. 
You can check it by going to the AWS Console -> AWS SES -> Identities. At this time you have successfully deployed infrastructure to 
send email notifications via SES, but your AWS account is in the Sandbox mode. When in Sandbox mode, you will have to verify each 
recipient email id manually. In order to get your SES account out of Sandbox, please follow the instructions in <a href="https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html">Moving out of Sandbox</a> .
Once your AWS SES account is out of sandbox you can send email to any recipient email id without any prior verification. 

### Monitoring for Email Bounces
When SES Stack is deployed during the pipeline stage, it will setup a <a href="https://docs.aws.amazon.com/ses/latest/dg/using-configuration-sets.html">configuration set</a>
which will send any email bounces, delivery failures, rejects & complaints to an SNS topic. In this step, you can add subscriptions to this SNS topic to monitor email delivery problems
In order to do that go to AWS Console -> SNS -> Select the SNS topic which would look like `{resource_prefix}-{envname}-SNS-Email-Bounce-Topic` ( where resource_prefix and envname are specified in the cdk.json ) -> Create Subscription. You can attach multiple subscriptions to
this SNS topic and monitor and take actions in case of any delivery failure.


## Additional resources - FAQs

### How does the `prod_sizing` field in `cdk.json` affect the architecture ?

This field defines the size of the backend resource. It is recommended to set it to `true` when deploying into a production environment, and `false` otherwise.
By setting the value to `true`, data.all backend resources are more available and scale faster.
When setting the value to `false`, backend resources become smaller but you save up on cost.

These are the resources affected:

| Backend Service |prod_sizing| Configuration
|-----------------|-----------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|Aurora           |true       | - Deletion protection enabled <br /> - Backup retention of 30 days <br /> - Paused after 1 day of inactivity <br /> - Max capacity unit of 16 ACU <br /> - Min capacity unit of 4 ACU                                              |
|Aurora           |false      | - Deletion protection disabled <br /> - No backup retention <br /> - Paused after 10 mintes of inactivity <br /> - Max capacity unit of 8 ACU <br /> - Min capacity unit of 2 ACU                                                  |
|OpenSearch       |true       | - The KMS key of the OpenSearch cluster is kept when the CloudFormation stack is deleted <br /> - Cluster configured with 3 master node and 2 data nodes <br /> - Each data node has an EBS volume of 30GiB attached to it         |
|OpenSearch       |false      | - The KMS key of the OpenSearch cluster gets deleted when the CloudFormation stack is deleted <br /> - Cluster configured with 0 master node and 2 data nodes <br /> - Each data node has an EBS volume of 20GiB attached to it    |
|Lambda function  |true       | - Lambda functions are configured with more memory                                                                                                                                                                                 |
|Lambda function  |false      | - Lambda functions are configured with less memory                                                                                                                                                                                 |

### I used the wrong accounts or made another mistake in the deployment. How do I un-deploy data.all?
In the above steps we are only deploying data.all tooling resources. Hence, if the CI/CD CodePipeline pipeline has not 
been entirely run, nothing has been deployed to the infrastructure account(s).

To clean-up the tooling account we have to simply delete the 2 AWS CloudFormation stacks deployed in the account:
- In your selected region: `<resource_prefix>-<git_branch>-cicd-stack`
- In us-east-1: `<resource_prefix>-<git_branch>-cicd-stack-support-us-east-1`

Some AWS resources have deletion particularities:
- Aurora Database for integration testing: deletion protection is enabled by default and will result in `DELETE_FAILED`
in AWS CloudFormation. Enable deletion in RDS before deleting `<resource_prefix>-<git_branch>-cicd-stack`. 
- KMS keys are marked as `pending deletion` and once the waiting period is over they are effectively deleted. This is
their default behavior explained in the [documentation](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html).
- The S3 buckets created by the deployment will not get deleted by AWS CloudFormation automatically, given these contain objects. Before running a new deployment, remove the S3 buckets matching the naming convention `<resource_prefix>-<git_branch>-cicd-stack-xxxxxxxxx` first to prevent a CloudFormation error reporting on already existing buckets.

### Troubleshooting - The CodePipeline Pipeline fails with CodeBuild Error Code "AccountLimitExceededException"
Sometimes, we run into the following error *"Error calling startBuild: Cannot have more than 1 builds in queue for the account"*.
Nothing is wrong with the code itself, CodeBuild quotas have been hit. Just click on **Retry**.

### I would like to migrate to Amazon OpenSearch Serverless
If you have deployed data.all with Amazon OpenSearch and would like to migrate to Amazon OpenSearch Serverless, 
you would need to migrate the indexes to your new cluster. Although data.all currently does not provide an automated 
migration tool, it is possible to do so manually using the following approaches:
- [Migrate your indexes to Amazon OpenSearch Serverless with Logstash](https://aws.amazon.com/blogs/big-data/migrate-your-indexes-to-amazon-opensearch-serverless-with-logstash/).
- [Migrating Amazon OpenSearch Service indexes using remote reindex](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/remote-reindex.html)
