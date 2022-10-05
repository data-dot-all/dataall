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

Finally, we need to add **Development environments**. These are the AWS accounts and regions where the infrastructure defined in the CICD pipeline
is deployed. 

!!! warning "environment ID = data.all environment stage"
      When creating the pipeline and adding development environments, you define the stage of the environment. The bootstrap `e` parameter needs to match the one that you define in the data.all UI.
      In our example, we bootstraped with the parameters "dev" and "prod" and then we defined the stages as "dev" and "prod" correspondingly.


![create_pipeline](pictures/pipelines/pip_create_form.png#zoom#shadow)

### data.all and DDK multi-account

#### CodeCommit repository

When a pipeline is created, a CloudFormation stack is deployed in the CICD environment AWS account. 
It contains an AWS CodeCommit repository with the code of an AWS DDK application set up for a multi-account deployment,
as explained in its [documentation](https://awslabs.github.io/aws-ddk/release/latest/how-to/multi-account-deployment.html).


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
In addition, the `app.py` file is also written accordingly to the development environments selected in data.all UI.

```

```
#### CICD deployment
data.all backend performs the first deployment of the CICD stack defined in the CodeCommit repository. The result is a
CloudFormation template deploying a CICD pipeline having the aforementioned CodeCommit repository as source.
This CodePipeline pipeline is based on the [CDK Pipelines library](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.pipelines/README.html)

## Cloning the repository
Pre-requisites:

1. Install git: `sudo yum install git`
2. Install pip: `sudo yum -y install python-pip`
3. Install git-remote-codecommit: `sudo pip install git-remote-codecommit`

Clone the repo:

4. Get the AWS Credentials from the AWS Credentials button in the Pipeline overview tab.
5. Clone the repository with the command in the overview tab.
    
![created_pipeline](pictures/pipelines/pip_overview.png#zoom#shadow)

