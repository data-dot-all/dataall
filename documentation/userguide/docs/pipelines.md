# **Pipelines**

Once the data is obtained, the processing of the data is difficult because of multiple and incompatible data sharing
mechanisms. Different business units might have their own data lake, the diversity of use cases need different tools:
Scikit Learn, Spark, SparkML, Sage Maker, Athena… and consequently, the diversity of tools and use-cases result in a
wide variety of CI/CD standards which difficult developing collaboration.

In order to distribute data ingestion and processing, data.all introduces data.all pipelines:

- data.all takes care of CI/CD infrastructure
- data.all integrates with <a href="https://awslabs.github.io/aws-ddk/">AWS DDK</a>

## Creating a pipeline
data.all pipelines are created from the UI, under Pipelines. Similar to the datasets, in the creation form of
the pipeline we have to specify:

- Name, Description and tags
- Environment and Team
- Development strategy: GitFlow or Trunk-based
- Development stages: dev, test, prod, qa,... It is required that at least "prod" is added.
- Template: it corresponds with the --template parameter that can be passed to DDK init command. See the <a href="https://awslabs.github.io/aws-ddk/release/latest/api/cli/aws_ddk.html#ddk-init">docs</a> for more details.
- From our the environment and team selected, we can choose whether this pipeline has an input or/and output dataset.

![create_pipeline](pictures/pipelines/pip_create_form.png#zoom#shadow)

When a pipeline is created, a CICD CloudFormation stack is deployed in the environment AWS account. 
It contains a CodePipeline pipeline (or more for GitFlow development strategy) that reads from an AWS CodeCommit repository.

In the first run of the CodePipeline Pipeline a DDK application is initialized in the Pipeline repository. This DDK app is deployed in the subsequent runs.
If you want to change the deploy commands in the AWS CodeBuild deploy stage, note that the buildspec of the CodeBuild step is part of the CodeCommit repository.


!!!abstract "GitFlow and branches"
      If you selected GitFlow as development strategy, you probably notices that the CodePipelines for non-prod stages fail in the first run because they cannot find their source.
      After the first successful run of the prod-CodePipeline pipeline, just create branches in the CodeCommit repository for the other stages and you are ready to go.

## Working with pipelines
### Cloning the repository
1. Install git: `sudo yum install git`
1. Install pip: `sudo yum -y install python-pip`
1. Install git-remote-codecommit: `sudo pip install git-remote-codecommit`
1. Setup credentials and clone you pipeline repository. Copy the Credentials from the AWS Credentials button in the Pipeline overciew tab.
    
![created_pipeline](pictures/pipelines/pip_overview.png#zoom#shadow)

### Environment variables
From the repository we can access the following environment variables:

![created_pipeline](pictures/pipelines/env_vars.png#zoom#shadow)

!!!abstract "No more hardcoding parameters"
      Use these environment variables in your code and avoid hardcoding IAM roles and S3 Bucket names. Use the ENVTEAM IAM role 
      to access the datasets of your team. With the input/output variables you can forget about checking the name of Glue databases and S3 Buckets.

## Deploying to multiple AWS accounts/Environments
By default, the DDK application is deployed in the same account as the CICD. The data pipelines that we build with DDK
constructs are deployed in the same environment account even when we define multiple development stages. 

Maybe in your enterprise you use one AWS account for CICD resources, and one AWS account for each of the development stages where you host the data pipelines.
In this scenario, in which you want to deploy the DDK application to different AWS accounts, this is our proposed approach:

### Setting up the environments

For example, the Data Science team has 3 AWS accounts: DS-DEV, DS-TEST and DS-PROD. In data.all we create 3 environments linked to each of these accounts: DS-DEV-Environment, DS-TEST-Environment and DS-PROD-Environment.
We also link the CICD account to data.all by creating the CICD-Environment.

DS-DEV, DS-TEST and DS-PROD accounts need to be bootstrapped with the following line, assuming 111111111111 = CICD account. The parameter -e needs to be set according to the stage of the account.

`ddk bootstrap -e dev -a 111111111111`

### Create pipeline

We create the pipeline in the CICD-Environment. The CICD stack will be deployed to the CICD account. Create the pipeline selecting with trunk-based + prod stage only. 

### Customize the ddk.json configuration file

We customize the ddk.json file in the CodeCommit repository. More info <a href="https://awslabs.github.io/aws-ddk/release/stable/how-to/multi-account-deployment.html">here</a>.  

```json
{
    "environments": {
        "cicd": {
            "account": "111111111111",
            "region": "us-west-2"
        },
        "dev": {
            "account": "222222222222",
            "region": "us-west-2",
            "resources": {
                "ddk-bucket": {"versioned": false, "removal_policy": "destroy"}
            }
        },
        "test": {
            "account": "333333333333",
            "region": "us-west-2",
            "resources": {
                "ddk-bucket": {"versioned": true, "removal_policy": "retain"}
            }
        }
    }
}
```
It self-mutates the stack and adds steps to deploy to the other accounts. DDK multiaccount strategy is trunk-based.
