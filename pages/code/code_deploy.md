---
layout: default_sublevel
title: Code - deploy
permalink: /code/code-deploy/
---
# **deploy**

We deploy the data.all tooling, backend and frontend using AWS Cloud Development Kit, which offers
high level abstractions to create AWS resources.

The deploy folder is a CDK application, with an `app.py` deploying a CICD stack. In the final deploy step of the
[Deploy to AWS](./deploy-aws/) guide, we are deploying the CICD pipeline stack defined in this section.


## stacks
As explained above, here is the code that defines the CICD pipeline in the tooling account. More specifically,
the `PipelineStack` is defined in `stacks/pipeline.py` 


From this stack, we deploy a CodePipeline pipeline and other stacks as standalone resources (e.g. `VpcStack` from `stacks/vpc.py`).
In addition, we define some CodePipeline deployment stages such as the stage that deploys 
the backend code `BackendStage` from `stacks/backend_stage`.

In the pipeline stack `PipelineStack` we deploy the following, which deploy the sub-stacks:
- `AlbFrontStage`
  - `AlbFrontStack`: Application Load Balancer for the UI applications
- `CloudfrontStage`
  - `Cloud`
- `BackendStage`
  - `BackendStack`: 
    - `AuroraServerlessStack`: Aurora RDS Database and associated resources - data.all objects metadata
    - `IdpStack`
    - `ContainerStack` 
    - `CloudWatchCanariesStack` if enable_cw_canaries=true
    - `CloudWatchRumStack` if enable_cw_run=true
    - `DBMigrationStack` 
    - `LambdaApiStack` 
    - `MonitoringStack` 
    - `OpenSearchStack`: OpenSearch cluster - data.all central catalog
    - `ParamStoreStack` 
    - `S3ResourcesStack` 
    - `SecretsManagerStack` 
    - `SqsStack` 
    - `VpcStack`
- `AuroraServerlessStack`: Aurora RDS Database and associated resources - for integration testing
- `CodeArtifactStack`
- `ECRStage`
- `VpcStack`



Finally, there are other elements in the `stacks` folder:
```
deploy/stacks/
├── cdk_nag_exclusions.py: define NAG exclusions in albfront and ....
├── aurora.py : the API GW
├── cognito.py : the use rpool
├── container.py : the ECS
├── container_standalone.py : the standalone ECS stack
├── data.all_standalone_stack.py : the webapp standalone stack
├── sqs.py: the sqs stack
├── lambdas.py : the lambda fx stack
├── pipeline.py : the data.all ci/cd pipeline stack
├── pyNestedStack.py : a nested stack interface
└── vpc.py  : the VPC Stack
```


## canaries

## configs

## custom_resources

## pivot_role


