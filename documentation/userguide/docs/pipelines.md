# **Pipelines**

Once the data is obtained, the processing of the data is difficult because of multiple and incompatible data sharing
mechanisms. Different business units might have their own data lake, the diversity of use cases need different tools:
Scikit Learn, Spark, SparkML, Sage Maker, Athena… and consequently, the diversity of tools and use-cases result in a
wide variety of CI/CD standards which difficult developing collaboration.

In order to distribute data ingestion and processing, data.all introduces data.all pipelines:

- data.all takes care of CI/CD infrastructure
- data.all integrates with <a href="https://awslabs.github.io/aws-ddk/">AWS DDK</a>
- data.all allows you to define development environments from the UI and deploys data pipelines to those AWS accounts

## Creating a pipeline
data.all pipelines are created from the UI, under Pipelines. Similar to the datasets, in the creation form of
the pipeline we have to specify:

- Name, Description and tags
- CICD Environment
- Team, this is the Admin team of the pipeline. It belongs to the specified CICD Environment where the pipeline is defined as IaC
- Development strategy: GitFlow or Trunk-based
- Template: it corresponds with the --template parameter that can be passed to DDK init command. See the <a href="https://awslabs.github.io/aws-ddk/release/latest/api/cli/aws_ddk.html#ddk-init">docs</a> for more details.

Finally, we need to add **Development environments**. These are the AWS accounts and regions where the infrastructure defined in the CICD pipeline
is deployed. 

![create_pipeline](pictures/pipelines/pip_create_form.png#zoom#shadow)

When a pipeline is created, a CICD CloudFormation stack is deployed in the CICD environment AWS account. 
It contains a CodePipeline pipeline (or more for GitFlow development strategy) that reads from an AWS CodeCommit repository.

In the first run of the CodePipeline Pipeline a DDK application is initialized in the Pipeline repository. This DDK app is deployed in the subsequent runs.
If you want to change the deploy commands in the AWS CodeBuild deploy stage, note that the buildspec of the CodeBuild step is part of the CodeCommit repository.


!!!warning "GitFlow and CodeCommit branches"
      If you selected GitFlow as development strategy, you probably noticed that the CodePipelines for non-prod stages fail in the first run because they cannot find their source.
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
      Use these environment variables in your code and avoid hardcoding IAM roles. Use the ENVTEAM IAM role 
      to access the datasets of your team

## Deploying to multiple AWS accounts/Environments
The default DDK application obtained by running `ddk init` is deployed in the same account as the CICD. However, we make it easy for you 
to deploy the application to multiple AWS accounts. 

Let's see it with an example. The Data Science team has 3 AWS accounts: DS-DEV, DS-TEST and DS-PROD. In data.all we create 3 environments linked to each of these accounts: DS-DEV-Environment, DS-TEST-Environment and DS-PROD-Environment.
We also link the CICD account to data.all by creating the DS-CICD-Environment.

### Pre-requisites
As a pre-requisite, DS-DEV, DS-TEST and DS-PROD accounts need to be bootstrapped trusting the CICD account and setting the stage of the AWS account with the  `e` parameter. Assuming 111111111111 = CICD account the commands are as follows:

- In DS-DEV (222222222222): `ddk bootstrap -e dev -a 111111111111`
- In DS-TEST (333333333333): `ddk bootstrap -e test -a 111111111111`
- In DS-PROD (444444444444): `ddk bootstrap -e prod -a 111111111111`

Once we have this trust, we create a data.all pipeline with these environments. Depending on the development strategy one or multiple 
CodePipeline pipelines are deployed, in any case they all reference a single CodeCommit repository. 
In this repository, data.all pushes a `ddk.json` file with the details of the selected development environments:

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
        },
        "prod": {
            "account": "444444444444",
            "region": "us-west-2",
            "resources": {
                "ddk-bucket": {"versioned": true, "removal_policy": "retain"}
            }
        }
    }
}
```

From here, we have 2 alternative ways of running the deployment to the different development accounts.
One is to use the data.all CICD pipeline(s) and the other is to create a DDK multi-environment CICD pipeline.


### Option 1: Using data.all CICD
In this approach we use the deployed CICD and modify the DDK application stack to be deployed in the correspondent environment.
There are other ways of implementing this logic, but here we propose one simple implementation:

Step 1: Create your own config based in the global configuration

```
### utils/config.py
from aws_ddk_core.config.config import Config
from typing import Dict


class DAConfig(Config):
    def __int__(self, *args, **kwargs) -> None:
        super.__init__(*args, **kwargs)

    def get_stage_env_id(
            self,
            stage_id: str,
    ) -> str:
        """
        Get environment id representing AWS account and region with specified stage_id.
        Parameters
        ----------
        stage_id : str
            Identifier of the stage
        Returns
        -------
        environment_id : str
        """
        environments = self._config_strategy.get_config(key="environments")

        for env_id, env in environments.items():
            if env.get('stage', {}) == stage_id:
                environment_id = env_id
                break
        else:
            raise ValueError(f'Environment id with stage_id {stage_id} was not found!')

        return environment_id

    def get_env_var_config(
        self,
        environment_id: str,
    ) -> dict:
        """
        Get environment specific variable from config for given environment id.
        Parameters
        ----------
        environment_id : str
            Identifier of the environment
        Returns
        -------
        config : Dict[str, Any]
            Dictionary that contains environmental variables for the given environment
        """
        env_vars = self.get_env_config(environment_id) | self._config_strategy.get_config('global')
        return env_vars
```

Step 2: Modify `app.py` to read the environment from the CodeBuild environment variables and the configuration from step 1

```
#!/usr/bin/env python3
import os
import aws_cdk as cdk
from ddk_app.ddk_app_stack import DdkApplicationStack

from utils.config import DAConfig

stage_id = os.environ.get('STAGE', None)
pipeline_name = os.environ.get('PIPELINE_NAME')

app = cdk.App()

config = DAConfig()
environment_id = config.get_stage_env_id(stage_id)
env_vars = config.get_env_var_config(environment_id)

DdkApplicationStack(app,
                    f"{pipeline_name}-DdkApplicationStack",
                    environment_id,
                    env_vars)

app.synth()
```


### Option2: Creating a DDK multi-environment CICD stack
Following the guide in the <a href="https://awslabs.github.io/aws-ddk/release/stable/how-to/multi-account-deployment.html">DDK docs</a>. 
From the guide, the only step that we need to do is the modification of the `app.py`. Once you push the changes a new CICD pipeline is deployed in a new CloudFormation stack.
!!!warning Naming!
      Don't forget to change the repository name to the one of our pipeline. Also, be careful with the name of the CICD pipeline stack, 
      you might update previously created stacks instead of creating a new one.

The DDK CICDPipeline construct is an opinionated construct that follows trunk-based development strategy only.
```
#!/usr/bin/env python3

import aws_cdk as cdk
from aws_ddk_core.cicd import CICDPipelineStack
from aws_ddk_core.config import Config
from ddk_app.ddk_app_stack import DdkApplicationStack

app = cdk.App()

class ApplicationStage(cdk.Stage):
    def __init__(
        self,
        scope,
        environment_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, f"Ddk{environment_id.title()}Application", **kwargs)
        DdkApplicationStack(self, "DataPipeline", environment_id)

config = Config()
(
    CICDPipelineStack(
        app,
        id="DdkCodePipeline-CHANGE-MY-NAME",
        environment_id="dev",
        pipeline_name="ddk-application-pipeline",
    )
    .add_source_action(repository_name="NAME-OF-THE-PIPELINE-REPO")
    .add_synth_action()
    .build()
    .add_stage("dev", ApplicationStage(app, "dev", env=config.get_env("dev")))
    .synth()
)

app.synth()

```

### Comparison
- With option 1 we can use GitFlow or Trunk-based dev strategies indistinctly, with option 2 only Trunk
- With option 1 we define CICD infrastructure from data.all, with option 2 we let users define the CICD infrastructure. To put is simple, option 1 promotes a standard CICD pipeline while option 2 allows more flexibility.
- Option 2 creates an extra CloudFormation stack and the data.all deployed pipeline(s) is obsolete.