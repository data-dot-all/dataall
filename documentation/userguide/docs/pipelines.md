# **Pipelines**

Different business units might have their own data lake and ingest and process the data with very different tools:
Scikit Learn, Spark, SparkML, AWS SageMaker, AmazonAthena… The diversity of tools and use-cases result in a
wide variety of CICD standards which discourages development collaboration.

In order to distribute data ingestion and processing, data.all introduces data.all pipelines:

- data.all takes care of CICD infrastructure
- data.all integrates with <a href="https://awslabs.github.io/aws-ddk/">AWS DDK</a>, a tool to help you build data workflows in AWS
- data.all allows you to define development environments directly from the UI and deploys data pipelines to those AWS accounts

!!! success "Focus on value-added code"
      data.all takes care of the CICD and multi-environment configuration and DDK provides reusable assets and data constructs that accelerate the deployment of AWS data workflows,
      so you can focus on writing the actual transformation code and generating value from your data!


## Multi-environment Pipelines
In some cases, enterprises decide to separate CICD resources from data application resources, which at the same time, need to be deployed to multiple accounts.
Data.all allows users to easily define their CICD environment and other infrastructure environments in a flexible, robust way.

Let's see it with an example. In your enterprise, the Research team has 3 AWS accounts: Research-CICD, Research-DEV and Research-PROD. They want to ingest data with a data pipeline that is written in Infrastructure-As-Code
in the Research-CICD account. The actual data pipeline is deployed in 2 data accounts. First, in Research-DEV for development and testing and once it is ready it is deployed to Research-PROD.


### Pre-requisites
As a pre-requisite, Research-DEV and Research-PROD accounts need to be bootstrapped trusting the CICD account (`-a` parameter) and setting the stage of the AWS account, the environment id, with the  `e` parameter. Assuming 111111111111 = CICD account the commands are as follows:

- In Research-CICD (111111111111): `ddk bootstrap -e cicd`
- In Research-DEV (222222222222): `ddk bootstrap -e dev -a 111111111111`
- In Research-PROD (333333333333): `ddk bootstrap -e prod -a 111111111111`

In data.all we need to link the AWS accounts to the platform by creating 3 data.all Environments: Research-CICD Environment, Research-DEV Environment and Research-PROD Environment.

### Creating a pipeline
data.all pipelines are created from the UI, under Pipelines. We need to fill the creation form with the following information:

- Name, Description and tags
- CICD Environment: AWS account and region where the CICD resources will be deployed.
- Team, this is the Admin team of the pipeline. It belongs to the specified CICD Environment where the pipeline is defined as IaC
- Development strategy: GitFlow or Trunk-based
- Template: it corresponds with the --template parameter that can be passed to DDK init command. See the <a href="https://awslabs.github.io/aws-ddk/release/latest/api/cli/aws_ddk.html#ddk-init">docs</a> for more details.

Finally, we need to add **Development environments**. These are the AWS accounts and regions where the infrastructure defined in the CICD pipeline
is deployed. 

!!! warning "environment ID = data.all environment stage"
      When creating the pipeline and adding development environments, you define the stage of the environment. The bootstrap `e` parameter needs to match the one that you define in the data.all UI.
      In our example, we boostraped with the parameters "dev" and "prod" and then we defined the stages as "dev" and "prod" correspondingly.


![create_pipeline](pictures/pipelines/pip_create_form.png#zoom#shadow)

### data.all CICD

When a pipeline is created, a CICD CloudFormation stack is deployed in the CICD environment AWS account. 
It contains a CodePipeline pipeline (or more for GitFlow development strategy) that reads from an AWS CodeCommit repository. 
The shape of the pipeline depends on the development strategy chosen and in the amount of development stages.

In the first run of the CodePipeline Pipeline a DDK application is initialized in the Pipeline repository. This DDK app is deployed in the subsequent runs.
If you want to change the commands that are run in the AWS CodeBuild deploy stage, note that the buildspec of the CodeBuild step is part of the CodeCommit repository.

!!!warning "GitFlow and CodeCommit branches"
      If you selected GitFlow as development strategy, you probably noticed that the CodePipelines for non-prod stages fail in the first run because they cannot find their source.
      After the first successful run of the prod-CodePipeline pipeline, just create branches in the CodeCommit repository for the other stages and you are ready to go.

![create_pipeline](pictures/pipelines/pip_codepipeline.png#zoom#shadow)

### Multi-env configuration
In the deployed repository, data.all pushes a `ddk.json` file with the details of the selected development environments:

```json
{
    "environments": {
        "cicd": {
            "account": "111111111111",
            "region": "eu-west-1"
        },
        "dev": {
            "account": "222222222222",
            "region": "eu-west-1",
            "resources": {
                "ddk-bucket": {"versioned": false, "removal_policy": "destroy"}
            }
        },
        "prod": {
            "account": "333333333333",
            "region": "eu-west-1",
            "resources": {
                "ddk-bucket": {"versioned": true, "removal_policy": "retain"}
            }
        }
    }
}
```

We also modified the default DDK `app.py` to read the Config from the `ddk.json` file and select the environment 
matching the stage defined in the CodeBuild environment variables.

```
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from aws_ddk_core.config.config import Config
from ddk_app.ddk_app_stack import DdkApplicationStack

stage_id = os.environ.get('STAGE', None)
pipeline_name = os.environ.get('PIPELINE_NAME')

app = cdk.App()

config = Config()
environment = config.get_env(stage_id)

if not environment:
    raise ValueError(f'Environment id with stage_id {stage_id} was not found!')

# We can also add environment variables, read them and pass them to the stack
# env_config = config.get_env_config(stage_id)

DdkApplicationStack(app,
                    f"{pipeline_name}-DdkApplicationStack",
                    stage_id)

app.synth()
```

!!! success "Parameters and account-dependent variables"
      You can use the `ddk.json` file not only to configure the AWS accounts and deployment details, but also to 
      configure parameters on the stacks, for example S3 Bucket names or Glue database names! You can read those
      variables using the get_env_config built-in function: `env_config = config.get_env_config(stage_id)`

### Note on DDK multi-environment deployment

From data.all we offer a simple ready-to-use multi-account deployment, but there are other ways of implementing the same logic. 
An alternative is the one proposed in the <a href="https://awslabs.github.io/aws-ddk/release/stable/how-to/multi-account-deployment.html">DDK guide for multi-account deployments</a>. 
From the guide, we need to bootstrap the accounts and modify the `app.py`. Once you push the changes a new CICD pipeline is deployed in a new CloudFormation stack.

!!! warning "Naming!"
      Don't forget to change the repository name to the one of our pipeline. Also, be careful with the name of the CICD pipeline stack, 
      you might update previously created stacks instead of creating a new one. Check the example below.

**Comparison**

- data.all default pipelines are simpler to implement: in the default data.all CICD, we define CICD infrastructure from data.all code; with DDK CICDPipelines 2 we let users define the CICD resources. With the data.all default pipelines, users don't have to modify the DDK code to create CICD resources, they can directly start working on the data pipeline stack. 
- DDK CICDPipeline offers additional methods and flexibility: the DDK construct comes with some interesting features, such as testing stages or monitoring. Users can define their own pipelines from scratch.
- DDK CICDPipeline creates an extra new CloudFormation stack and the existing deployed CICD pipeline(s) is obsolete. 
- The DDK CICDPipeline construct is an opinionated construct that follows trunk-based development strategy only. Hence, you would typically use data.all default pipelines if GitFlow adapts better to your needs.

## Single-environment pipelines
Maybe you don't want to use multiple accounts for your code and your infrastructure. In such case, in the pipeline creation form 
select the same data.all Environment as the CICD environment and for the development stages.

You still need to bootstrap the AWS account with the following command: `ddk bootstrap`


## Cloning the repository
Pre-requisites:

1. Install git: `sudo yum install git`
2. Install pip: `sudo yum -y install python-pip`
3. Install git-remote-codecommit: `sudo pip install git-remote-codecommit`

Clone the repo:

4. Get the AWS Credentials from the AWS Credentials button in the Pipeline overview tab.
5. Clone the repository with the command in the overview tab.
    
![created_pipeline](pictures/pipelines/pip_overview.png#zoom#shadow)

