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

Let's see it with an example. In your enterprise, the Research team has 3 AWS accounts: Research-CICD, Research-DEV and Research-PROD. They want to ingest data with a data pipeline that is written in Infrastructure as Code (IaC)
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
- CICD strategy: This is the development strategy that determines the type of CICD Pipeline that is created by data.all. Currently the following 4 types are supported depending on your use case:
    1. [**CDK Pipelines - Trunk-based**](#CDK-Pipelines-Overview) : A CICD pipeline based on [CDK Pipelines library](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/README.html). It defines a DDK Core construct which deploys Continuous Integration and Delivery for your app. Specifically, it provisions a stack containing a self-mutating CDK code pipeline to deploy one or more copies of your CDK applications using CloudFormation with a minimal amount of effort on your part.
    2. [**CodePipeline - Trunk-based**](#CodePipeline-pipelines---Trunk-based-or-GitFlow-Overview) : A CICD pipeline similar to CDK Pipelines and with a trunk-based approach but is not self-mutating.
    3. [**CodePipeline - Gitflow**](#CodePipeline-pipelines---Trunk-based-or-GitFlow-Overview): A Gitflow branching strategy where each branch of the source repository has a corresponding CICD Pipeline that deploys resources for that branches environment.

Finally, we need to add **Development environments**. These are the AWS accounts and regions where the infrastructure defined in the CICD pipeline
is deployed. 

!!! warning "environment ID = data.all environment stage"
      When creating the pipeline and adding development environments, you define the stage of the environment. The ddk bootstrap `-e` parameter needs to match the one that you define in the data.all UI.
      In our example, we bootstraped with the parameters "dev" and "prod" and then we defined the stages as "dev" and "prod" correspondingly.


![create_pipeline](pictures/pipelines/pip_create_form.png#zoom#shadow)

---

### CDK Pipelines Overview

#### CodeCommit repository

When a pipeline is created, an AWS CodeCommit repository with the code of an AWS DDK application is created in the CICD environment AWS account. It contains an  set up for a multi-account deployment, as explained in its [documentation](https://awslabs.github.io/aws-ddk/release/latest/how-to/multi-account-deployment.html).


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
In addition, the `app.py` file is also written accordingly to the development environments selected in data.all UI. It will look similar to the following:

```

# !/usr/bin/env python3

import aws_cdk as cdk
from aws_ddk_core.cicd import CICDPipelineStack
from ddk_app.ddk_app_stack import DDKApplicationStack
from aws_ddk_core.config import Config

app = cdk.App()

class ApplicationStage(cdk.Stage):
    def __init__(
            self,
            scope,
            environment_id: str,
            **kwargs,
    ) -> None:
        super().__init__(scope, f"dataall-{environment_id.title()}", **kwargs)
        DDKApplicationStack(self, "DataPipeline-PIPELINENAME-PIPELINEURI", environment_id)

config = Config()
(
    CICDPipelineStack(
        app,
        id="dataall-pipeline-PIPELINENAME-PIPELINEURI",
        environment_id="cicd",
        pipeline_name="PIPELINENAME",
    )
        .add_source_action(repository_name="dataall-PIPELINENAME-PIPELINEURI")
        .add_synth_action()
        .build().add_stage("dev", ApplicationStage(app, "dev", env=config.get_env("dev"))).add_stage("prod", ApplicationStage(app, "prod", env=config.get_env("prod")))
        .synth()
)

app.synth()


```
#### CICD deployment
data.all backend performs the first deployment of the CICD stack defined in the CodeCommit repository. The result is a CloudFormation template deploying a CICD pipeline having the aforementioned CodeCommit repository as source. This CodePipeline pipeline is based on the [CDK Pipelines library](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/README.html). 

![create_pipeline](pictures/pipelines/pip_cdk_trunk.png#zoom#shadow)

---

### CodePipeline pipelines - Trunk-based or GitFlow Overview

For cases in which we do not want to use [CDK Pipelines library](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/README.html) we can instead
use CodePipeline CICD Strategy which leverages the [aws-codepipeline](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_codepipeline-readme.html) construct library. 


#### CodeCommit repository and CICD deployment
When a pipeline is created, a CloudFormation stack is deployed in the CICD environment AWS account. It contains:

- an AWS CodeCommit repository with the code of an AWS DDK application (by running `ddk init`) with some modifications to allow cross-account deployments.
- CICD CodePipeline(s) pipeline that deploy(s) the application

The repository structure will look similar to:

![created_pipeline](pictures/pipelines/pip_cp_init2.png#zoom#shadow)

The added `Multiaccount` configuration class allows us to define the deployment environment based on the `ddk.json`. 
Go ahead and customize this configuration further, for example you can set additional `env_vars`.

Trunk-based pipelines append one stage after the other and read from the main branch of our repository:

![created_pipeline](pictures/pipelines/pip_cp_trunk.png#zoom#shadow)

Gitflow strategy uses multiple CodePipeline pipelines for each of the stages. For example if you selected `dev` and `prod`:

![created_pipeline](pictures/pipelines/pip_cp_gitflow.png#zoom#shadow)

The `dev` pipeline reads from the `dev` branch of the repository:

![created_pipeline](pictures/pipelines/pip_cp_gitflow2.png#zoom#shadow)

---
## Editing a Data All Pipeline

For users who would like to promote their pipeline deployments to new environments managed by data all, you can do so by first bootstrapping the new environment(s) to be deployed to (as mentioned in the [Pre-requisites](#Pre-requisites)) and then adding and/or editing the development environments.

![edit_pipeline](pictures/pipelines/pip_edit_form.png#zoom#shadow)

Based on pipeline use case, editing a data all pipeline's development environments will:
- **CDK Pipelines**: On update, the `ddk.json` and `app.py` will be edited to update the new development environment information. The self-mutating, CICD Pipeline will trigger and deploy to the new environments based on the source CodeCommit repository changes.
- **CodePipelines - Trunk-based**: On update the `ddk.json` will be edited. A new `cdk deploy` will run to update the CICD CloudFormation Stack for the AWS CodePipeline to add the new stages required for the additional environment deployment(s) (as well as manual approval steps between stages in the code pipeline). You will see these updates to the CICD stack in CloudFormaiton of the CICD environment.
- **CodePipelines - Gitflow**: On update the `ddk.json` will be edited. A new `cdk deploy` will run to update the CICD CloudFormation Stack to add the new AWS CodePipelines required for the additional environment deployment(s). You will see these updates to the CICD stack in CloudFormaiton of the CICD environment.

## Which development strategy should I choose?

**CDK pipelines - Trunk-based**

1. The `CDK-pipelines` construct handles cross-account deployments seamlessly and robustly. It synthesizes CDK stacks as CloudFormation stacks and performs the deployment cross-account. Which means that we don't manually assume IAM roles in the target accounts, all is handled by CDK :)
2. It also allows developers to modify the CICD stack as it is self-mutating. It is easy to customize having several typical CodePipeline stages out-of-the-bix. For example, developers can add monitoring, tests, manual approvals directly in the repository with single-line changes.

**CodePipeline pipelines - Trunk-based or GitFlow**

1. The `aws-codepipelines` construct uses AWS CodePipelines directly. We are able to define any type of CICD architecture, such as in this case Trunk-based and GitFlow.
2. Developers working on the pipeline cannot modify the CICD pipeline
3. Cross-account deployments require specific definition of the environment in the code.


**Summary**

CDK pipelines are recommended for flexibility and for a robust cross-account application deployment, whereas CodePipeline pipelines are recommended if you need to provide an immutable pipeline architecture or if you want to implement a GitFlow strategy.


## Cloning the repository
Pre-requisites:

1. Install git: `sudo yum install git`
2. Install pip: `sudo yum -y install python-pip`
3. Install git-remote-codecommit: `sudo pip install git-remote-codecommit`

Clone the repo:

4. Get the AWS Credentials from the AWS Credentials button in the Pipeline overview tab.
5. Clone the repository with the command in the overview tab.
    
![created_pipeline](pictures/pipelines/pip_overview.png#zoom#shadow)

