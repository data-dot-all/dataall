# **Pipelines**

Once the data is obtained, the processing of the data is difficult because of multiple and incompatible data sharing
mechanisms. Different business units might have their own data lake, the diversity of use cases need different tools:
Scikit Learn, Spark, SparkML, Sage Maker, Athena… and consequently, the diversity of tools and use-cases result in a
wide variety of CI/CD standards which difficult developing collaboration.

In order to distribute data processing, data.all introduces data.all pipelines where:
- data.all takes care of CI/CD infrastructure
- data.all offers flexible pipeline blueprints to deploy AWS resources and a Step Function

## Creating a pipeline
data.all pipelines are created from the UI, under "Automate Pipeline". Similar to the datasets, in the creation form of
the pipeline we have to specify:
- Environment
- Group: Users inside this environment-group will be able to see and access the pipeline in the list of pipelines in
- the UI.
- Name, Description and tags
- Template: currently 2 different templates, "SageMaker pipeline" and "General pipeline" (more details below)
- Stages: "Deploy to PROD account only" or "Deploy to ALL accounts" (more details below)

[INSERT IMAGE]

When a pipeline is created, various CloudFormation stacks are deployed:
- One stack holds the CICD resources: CodePipeline pipeline + CodeCommit repository among others
- Another stack that creates a Step Function and AWS resources defined in the pipeline CodeCommit repository.

The content of the CodeCommit repository is the directory that is used as a base for data.all Data/ML Projects.
Upon creation of the project, the content is copied from the data.all backend repo to the business account repository.
Depending on the specifications defined on the pipeline repository, different resources and a different step function
gets deployed by the second Cloud Formation stack. Details on how to use and develop on top of the blueprint are
included in the blueprint section.

#### CodePipeline stages
If we select deploy to PROD only, then we would deploy one CICD CloudFormation stack that creates a 5-stages AWS
CodePipeline pipeline that:
1. reads the pipeline CodeCommit repository
2. deploys the resources (standalone resources + step function) in a test stage
3. runs unit tests on the code
4. waits for manual approval
5. deploys the resources (standalone resources + step function) in a production stage

In step 2 and 5 of the CodePipeline pipeline we are deploying the StepFunction+resources CloudFormation stack.
Note that all the stacks (CICD and StepFunction+resources) stay in the Production account of the selected environment.

[INSERT IMAGE]

### Template
The previous explanation and stages inside the CICD CodePipeline pipeline refer to the "General pipeline" template.
This template can be used for general data processing workflows. Besides the General pipeline, data.all provides a
template for ML projects, a "SageMaker pipeline" template that includes additional steps in the CICD pipeline, so
that it:
1. reads the pipeline CodeCommit repository
2. **builds SageMaker Jobs**
3. **deploys Docker Images**
2. deploys the resources (standalone resources + step function) in a test stage
3. runs unit tests on the code
4. waits for manual approval
5. deploys the resources (standalone resources + step function) in a production stage

## Cloning the repository
1. Install git: **sudo yum install git**
1. Install pip: **sudo yum -y install python-pip**
1. Install git-remote-codecommit: **sudo pip install git-remote-codecommit**
1. Setup credentials and clone you pipeline repository:
    - Go to data.all UI ==> Pipeline ==> Click on your pipeline ==> Code ==> Get Credentials ==>
    - Copy paste the commands and execute in your terminal


## Executing the step function - who runs the step function?
The role assumed by the step function is a basic developer role for the env-group selected, which means that, if the
step function reads data from a data.all dataset a sharing request has to be done for this environment-group. In case
of doubts, the role can be accessed in the AWS Step Functions console.

*Clarification*: Does this mean that we only can create pipelines with basic-dev roles? No. It means that the IAM role
assumed by the step function is relative to  the environment-group selected (this can be admin,fulldev or basicdev in
the environment), but it has basicdev role permissions.
