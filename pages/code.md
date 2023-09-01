---
layout: default
homePage: false
title: Code Walkthrough
permalink: /code/
---
# **Code Walkthrough**

The data.all package is a mono-repo comprising several modules:

- [deploy/](#deploy)
- [backend/](#backend)
  - [base/](#base)
    - db
    - api
    - cdkproxy
  - [core/](#core)
    - Feature toogle
    - Permisisons
    - WorkerHandler
    - Stack helper
  - [modules/](#core)
    - db
    - aws
    - handlers
    - cdk
    - api
    - services
    - indexers
    - tasks
    - `__init__` and module loading
- [frontend/](#frontend)
  - [src/](#src)
    - [authentication/](#authentication)
    - [design/](#design)
    - [globalErrors/](#globalErrors)
    - [modules/](#modules)
      - Administration
      - Catalog
      - Dashboards
      - Datasets
      - Environments
      - Folders
      - Glossaries
      - MLStudio
      - Notebooks
      - NotFound
      - Organizations
      - Pipelines
      - [Shared](#shared)
      - Shares
      - Tables
      - Worksheets
    - [services/](#services)
      - graphql
      - hooks
    - [utils/](#utils)
      - helpers
    - [jsconfig.json](#jsconfig)
- [tests/](#tests)
- [compose/](#compose)
- [documentation/](#userguide)

## deploy/ <a name="deploy"></a>
We deploy the data.all tooling, backend and frontend using AWS Cloud Development Kit, which offers
high level abstractions to create AWS resources.

The `deploy` package is a CDK application, with an `app.py` deploying a CICD stack. In the final deployment step of the
[Deploy to AWS](./deploy-aws/) guide, we are deploying the CICD pipeline stack defined in this section.


### stacks
As explained above, here is the code that defines the CICD pipeline in the tooling account. More specifically,
the `PipelineStack` is defined in `stacks/pipeline.py` 

From this stack, we deploy a CodePipeline pipeline and other stacks as standalone resources (e.g. `VpcStack` from `stacks/vpc.py`).
In addition, we define some CodePipeline deployment stages such as the stage that deploys 
the backend code `BackendStage` from `stacks/backend_stage`.

In the pipeline stack `PipelineStack` we deploy the following stacks and sub-stacks:
- `AlbFrontStage`
  - `AlbFrontStack`: Application Load Balancer for the UI applications
- `CloudfrontStage`
  - `CloudFrontStack`: CloudFront UI
- `BackendStage`
  - `BackendStack`: 
    - `AuroraServerlessStack`: Aurora RDS Database and associated resources - data.all objects metadata
    - `IdpStack`: Cognito and IdP stack
    - `ContainerStack`: ECS stack ----> contains the ECS task definitions which are defined in backend.core and backend.modules
    - `CloudWatchCanariesStack` if enable_cw_canaries=true
    - `CloudWatchRumStack` if enable_cw_run=true
    - `DBMigrationStack`: tool to migrate between Aurora versions of the database table schemas
    - `LambdaApiStack` : Lambda Function stack
    - `MonitoringStack` : CloudWatch alarms and monitoring resources
    - `OpenSearchStack`: OpenSearch cluster - data.all central catalog (default)
    - `OpenSearchServerlessStack`: OpenSearch Serverless collection - data.all central catalog (if enabled)
    - `ParamStoreStack` : AWS SSM parameters
    - `S3ResourcesStack` : S3 resources
    - `SecretsManagerStack` : AWS SSM Secrets
    - `SqsStack` : SQS
    - `VpcStack`: Backend VPC and Networking Componenets (e.g. subnets, security groups, service endpoints, etc.)
- `AuroraServerlessStack`: Aurora RDS Database and associated resources - for integration testing
- `CodeArtifactStack`: for our Docker Images
- `ECRStage`: for our Docker Images
- `VpcStack`: Tooling VPC and Networking Componenets (e.g. subnets, security groups, service endpoints, etc.)

There are other elements in the `deploy` folder:
```
deploy/
├── pivot_role/  : with the YAML template for the data.all IAM Pivot Role (manually created)
├── cdk_exec_role/  : with the template for an optional role that can be used to bootstrap environments in cdk bootstrap 
├── configs/ : scripts that create configuration files for Cognito, CloudFront and CloudWatch RUM
├── custom_resources/ : resources or actions not included in CloudFormation
└── canaries/: scripts for canary used in Canary stack if CloudWatch canary is enabled
```

## backend/ <a name="backend"></a>
In this section we will touch upon the main components of the backend code. Here is a short description of all the components
and in the subsections we detail the structure of the `dataall` package.
```
backend/
├── dataall/  : application package (explained in detail below) 
├── docker/  :  Dockerfiles deployed in ECR (/prod) and used in docker compose locally (/dev)
├── migrations/ : scripts used by alembic to update the Aurora RDS database tables. README explaining details.
├── alembic.ini : used in database migrations
├── api_handler.py : GraphQL Lambda handler
├── aws_handler.py : Worker Lambda handler
├── search_handler.py :  ESProxy Lambda handler
├── cdkproxymain.py : ECS CDK task
├── local_cdkapi_server.py : CDKProxy local server used in docker (replacing the cdkproxymain)
├── local_graphql_server.py : Graphql local server used in docker (replacing the api_handler)
├── requirements.txt : requirements file used in Docker images for Lambdas and local containers of the backend
```
Inside `dataall/` we have 3 main sub-packages:
- base - common code used in core and modules
- core - components that are needed to operate data.all correctly
- modules - additional plug-in components that can be configured or disabled

### base/ <a name="base"></a>
The base package is divided into the listed components. We explain `db`, `api` and `cdkproxy` in more detail 
in each of their subsections.
```
base/
├── api/  : gql wrapper package. Constants and context definition.
├── aws/  :  wrapper client upon boto3 calls used across several modules (e.g. IAM class).
├── cdkproxy/ : CDK application that deploys stacks in environment accounts exposing a REST API.
├── db/ : configuration, connection parameters and base utilities for the RDS Aurora database
├── searchproxy/ : connection and search utils for the OpenSearch cluster
├── utils/ : generic utilities
├── __init__.py
├── config.py : Config class to manage the config.json file
├── context.py : Class to manage the API calls context
├── loader.py : Classes and methods that manage the loading of modules
```

#### db

Backend code relies on the popular Python's `sqlalchemy` ORM package to connect and perform operations
against the RDS database. Among other components in `base.db` we export:

1. `get_engine(envname='local')` : returns a wrapper for a SQLAlchemy  engine instance
2. `Base` : a SQL alchemy Base metadata class
3. `Resource` :  a SQL alchemy class that holds common fields (label, created,...) found in data.all models
4. `create_schema_and_tables` :  a method that will create schema and tables

#### api
The api is exposed using the [`ariadne` GraphQL package](https://ariadnegraphql.org/). 
The overall flow of GraphQL resolution is  found in the `app.py` module using the [`graphqlsync`](https://ariadnegraphql.org/docs/0.4.0/api-reference#graphql_sync)  from `ariadne`.

The data.all `base.api` package contains the `gql` sub-package to support GraphQL schemas. It is used to programmatically define GraphQL constructs.

#### cdkproxy
This package contains the code associated with the deployment of CDK stacks that correspond to data.all resources.
`cdkproxy` is a package that exposes a REST API to run registered cloudformation stacks using AWS CDK. It is deployed as a docker container running on AWS ECS.

When a data.all resource is created, the API sends an HTTP request 
to the docker service and the code runs the appropriate stack using `cdk` cli.

These stacks are deployed with the `cdk` cli wrapper
The API itself consists of 4 actions/paths:

- GET / : checks if the server is running
- POST /stack/{stackid} : creates or updates the stack
- DELETE /stack/{stackid} : deletes the stack
- GET /stack/{stackid] : returns stack status

The webserver is running on docker, using Python's  [FASTAPI](https://fastapi.tiangolo.com/) 
web framework and running using [uvicorn](https://www.uvicorn.org/) ASGI server.

### core/ <a name="core"></a>
Core contains those functionalities that are indispensable to run data.all. Customization of the core should be limited
as it affects downstream functionalities.

- activity
- cognito_groups
- environment
- notifications
- organizations
- permissions
- stacks
- tasks
- vpc

These "core-modules" follow a similar structure composed of the listed sub-components. 
Note that not all the sub-components are present in all core-modules.
```
core-module/
├── api/  : api definition and validation (in resolvers)
├── aws/  :  wrapper client upon boto3 calls
├── cdk/  :  CDK stacks to be deployed
├── db/ : models (database table models) and repositories (database operations)
├── handlers/ : code that will be executed in AWS Worker lambda (short-living tasks)
├── services/ : business logic
├── tasks/ : code that will be executed in ECS Tasks (long-living tasks)
├── __init__.py
├── any additional functionality
```
The sub-packages `api`, `db` and `cdk` are better explained in the modules/ section. Here, we will focus
on those core additional functionalities that are used by all modules: Feature toggle, Permissions, WorkerHandler and Stack helper.

#### Feature toggle
In `core/feature_toggle_checker` you will find a decorator that allows users to enable or disable certain
API calls from the core functionalities or the modules functionalities. This is useful whenever a customer wants to disable a particular feature
on the server side. For example, in the following case the `config.json` file has disabled a feature called `env_aws_actions`.

```json
    "core": {
        "features": {
            "env_aws_actions": true
        }
    }
```

If we go to the `core.environment.api` package we will see that some resolvers have been decorated depending on this flag.
Any resolver, any api call, can be enabled or disabled by introducing more core-toggle features in both the core and/or the modules.
```
@is_feature_enabled('core.features.env_aws_actions')
def _get_environment_group_aws_session(
    session, username, groups, environment, groupUri=None
):
...
```

#### Permissions
The `core.permissions` package implements the permission logic for the application and adds the permissions for the core modules.
In particular, `permission_checker.py` contains the decorators that validate the user permissions with respect to a resource.
- `db/` - the RDS tables and operations with RDS
- `api/` - the calls related to permissions
- `permissions.py` - the core module permission definitions

#### WorkerHandler
In `core/tasks/service_handlers.py` we defined the `WorkerHandler` Python class, that routes tasks 
to the Worker AWS Lambda (for tasks that are processed asynchronously).

This class has a singleton instance called `Worker`. It exposes a decorator function to register handler 
functions that can be run by the Worker. 

```
    @staticmethod
    @Worker.handler(path='SOMEPATH')
    def FUNCTION_NAME(engine, task: Task):
```

We use the 2 apis of the `Worker` class to send tasks to the Lambda and use the corresponding registered handler.

1. `Worker.queue(engine, task_ids: [str]))`: an interface to send a list of task ids to the worker
2. `Worker.process(engine, task_ids: [str])`: an interface to pick up and process a list of tasks

In the corresponding API call where you want to trigger the Worker Lambda, create a Task in RDS and queue it as in the following example.
```
        task = models.Task(
            targetUri=OBJECTURI,
            action='SOMEPATH',
            payload={.....},
        )
        session.add(task)
        session.commit()

        Worker.queue(engine=context.engine, task_ids=[task.taskUri])
```

Then, the Worker AWS Lambda receives JSON objects with the Task fields. Below is the code of the Worker Lambda defined in
`backend/aws_handler.py`.

```
def handler(event, context=None):
    """Processes  messages received from sqs"""
    log.info(f'Received Event: {event}')
    for record in event['Records']:
        log.info('Consumed record from queue: %s' % record)
        message = json.loads(record['body'])
        log.info(f'Extracted Message: {message}')
        Worker.process(engine=engine, task_ids=message)
```


Finally, the `WorkerHandler` will `process` the tasks by reading the task metadata from the RDS Database, routing to 
the decorated handler function 
and assuming a role in the AWS Account where the action needs to be performed.

If you want to see an example check the `core.stacks` or "Stack helper" package which contains a number of CloudFormation handlers.

#### Stack helper
The `core.stacks` package implements handlers, database logic and apis to manage CloudFormation (CDK) stacks that belong to a data.all module
(core module or plugable module). Some of the activities that it implements are:
- trigger the deployment of stacks
- describe status of stacks
- deletion of stacks
- record/look-up metadata about stacks in RDS


### modules/ <a name="modules"></a>

Modules are components that can be plugged in (or out) of your data.all deployment. Their features are configured in
the `config.json` file. In contrast to the `core` package, `modules` are meant to be customized and enriched with new
features. You can even go ahead and customize or create new modules.

Each module can contain all or a subset of the listed sub-packages:

```
module/
├── api/  : api definition and validation (in resolvers)
├── aws/  :  wrapper client upon boto3 calls
├── cdk/  :  CDK stacks to be deployed
├── db/ : models (database table models) and repositories (database operations)
├── handlers/ : code that will be executed in AWS Worker lambda (short-living tasks)
├── indexers/ : code to handle upsert/delete operations of data.all resources to the OpenSearch Catalog
├── services/ : business logic
├── tasks/ : code that will be executed in ECS Tasks (long-living tasks)
├── __init__.py
```

#### db

This package processes all requests to the RDS database for the module metadata, 
it can be from the Lambda API Handler, Lambda Worker or the ECS tasks.

The package contains 2 types of classes:
- Suffixed with `_models`: it defines tables and their schemas in our Aurora RDS database.
- Suffixed with `_repositories`: api calls against the RDS Aurora database.

Database data operations done by the backend rely on the popular Python's `sqlalchemy` ORM package. Here is an example 
of a query to find all deleted tables of a specific data.all dataset.
```
    @staticmethod
    def find_all_deleted_tables(session, dataset_uri):
        return (
            session.query(DatasetTable)
            .filter(
                and_(
                    DatasetTable.datasetUri == dataset_uri,
                    DatasetTable.LastGlueTableStatus == 'Deleted',
                )
            )
            .all()
        )
```
#### indexers
This package is required for modules that need to interact with the OpenSearch Catalog. It leverages the 
`BaseIndexer` class to implement the different upsert and delete operations in the catalog.


#### aws

The `aws` package is where all the AWS logic is implemented. It serves 
as an interface that performs API calls to AWS services. In other words, if a module performs calls 
to a particular AWS service, the corresponding boto3 client should be declared in the module `aws` package.
We recommend to leverage the `SessionHelper` class defined in `dataall.base.aws.sts` to start a session with 
the dataallPivotRole or any other role in the environment account.


#### handlers

Please review the section dedicated to `WorkerHandler` in /core. As explained, AWS Worker Lambda handlers are
registered by decorating them. The handlers package of each module contains the different handlers for the module.
They often use the `db` repositories and `aws` clients as it happens in the `DatasetProfilingGlueHandler` that uses
`DatasetRepository` and `GlueDatasetProfilerClient`.


```
    @staticmethod
    @Worker.handler('glue.job.profiling_run_status')
    def get_profiling_run(engine, task: Task):
        with engine.scoped_session() as session:
            profiling: DatasetProfilingRun = (
                DatasetProfilingRepository.get_profiling_run(
                    session, profiling_run_uri=task.targetUri
                )
            )
            dataset: Dataset = DatasetRepository.get_dataset_by_uri(session, profiling.datasetUri)
            status = GlueDatasetProfilerClient(dataset).get_job_status(profiling)

            profiling.status = status
            session.commit()
            return {"profiling_status": profiling.status}

```

#### tasks

In this package you should define the module ECS long-running tasks. For example, the ECS task
definition to run the sharing of datasets is placed in `dataset_sharing.tasks.share_manager`.

In addition, the task needs to be defined in the deployment of the ECS tasks. Here is an extract of
`deploy/stacks/container.py` where that particular task is defined. Use the `run_if` decorator to
set its dependency with a certain module.

```
    @run_if("modules.datasets.active")
    def add_share_management_task(self):
        share_management_task_definition = ecs.FargateTaskDefinition(
            self,
            f'{self._resource_prefix}-{self._envname}-share-manager',
            cpu=1024,
            memory_limit_mib=2048,
            task_role=self.task_role,
            execution_role=self.task_role,
            family=f'{self._resource_prefix}-{self._envname}-share-manager',
        )

        share_management_container = share_management_task_definition.add_container(
            f'ShareManagementTaskContainer{self._envname}',
            container_name=f'container',
            image=ecs.ContainerImage.from_ecr_repository(
                repository=self._ecr_repository, tag=self._cdkproxy_image_tag
            ),
            environment=self._create_env('DEBUG'),
            command=['python3.8', '-m', 'dataall.modules.dataset_sharing.tasks.share_manager_task'],
            ...
```

#### cdk
Under this directory you will find 4 different types of classes used in CDK deployments of infrastructure.
- resource stacks
- environment extensions
- environment team role policies (usually called `env_role_XXX_policy`)
- pivot role policies (usually called `pivot_role_XXX_policy`)

**Resource stacks**

Resource stacks, are CDK stacks deployed when a resource is created. For example, when we create a Dataset we deploy
the stack defined in `dataset_stack.py` and decorated as follows. The decorator and the stack manager are implemented
in `base.cdkproxy`.

```
@stack(stack='dataset')
class DatasetStack(Stack):
    ...
```

**Environment extensions**

For some modules, the environment stack includes base resources that are used for all users in the 
environment account. Taking the example of the `mlstudio` module, we see that in `cdk/mlstudio_stack.py`
we define a class that uses the base class `EnvironmentStackExtension`. This class requires the definition of
a function called `extent`, that "extends" the resources created by the environment stack with the module-specific
resources. In this case we add the SageMaker domain to the environment stack.

```
class SageMakerDomainExtension(EnvironmentStackExtension):

    @staticmethod
    def extent(setup: EnvironmentSetup):
        _environment = setup.environment()

```

**Environment team role policies**

If a team is invited to an environment and the module is enabled for that particular team, data.all creates
an IAM role as part of the environment cdk stack. That IAM role has different permissions depending on the 
features that it has access to. Those features often correspond to modules. In the Environment team role policies files
is where we define these policies that need to be added to a team IAM role if the feature is enabled for its team.

The IAM policy statements need to be defined creating a class that inherits the `ServicePolicy` class. Here is an example,
if the `dataset` module is active and a data.all Team has the `CREATE_DATASET` permissions the 
`DatasetDatabrewServicePolicy.get_statements` returned statements will be added to the team IAM policies.

```
class DatasetDatabrewServicePolicy(ServicePolicy):
    """
    Class including all permissions needed to work with AWS DataBrew.
    """
    def get_statements(self, group_permissions, **kwargs):
        if CREATE_DATASET not in group_permissions:
            return []

        statements = [
              ....

```

**Pivot role policies** 

We want the dataallPivotRole to follow least-privilege permissions and have only those IAM statements that are needed
to operate a certain configuration of data.all. Imagine that you disable the `dashboards` module, in that case, the 
pivotRole should not have any Quicksight related permissions needed by Dashboards. We achieve this modular definition
of pivotRole policies by using the `PivotRoleStatementSet` class to define the policies needed by the pivotRole for a module.
If the module is enabled, then the auto-created pivotRole is deployed with the additional PivotRoleStatementSet and viceversa.


```
class DatasetsPivotRole(PivotRoleStatementSet):
    """
    Class including all permissions needed  by the pivot role to work with Datasets based in S3 and Glue databases
    It allows pivot role to:
    - ....
    """
    def get_statements(self):
        statements = [
```


#### api

The `api` package depends on `base.api` and defines the API calls executed by the GraphQL Lambda handler.
You might have one single group of API calls or split them in multiple packages. Independently if you have a single package (e.g. `dashboards.api`) or multiple packages (e.g. `datasets.api`), 
each package should always follow the same structure:

1. `types.py` :  definition of GraphQL ObjectTypes
2. `mutations.py` : definition of GraphQL MutationFields --> API calls that modify an ObjectType
3. `queries.py` : definition of GraphQL QueryFields for the --> API calls that query information about an ObjectType
3. `input_types.py` : definition of GraphQL InputTypes used as input for MutationFields and QueryFields
4. `resolvers.py` : code that is executed in the MutationFields and QueryFields API calls. Input validation, no business logic.
5. (optional) `enums.py`: enums used in ObjectTypes and InputTypes

**Note:** all these classes need to be imported in the `module.api.__init__.py`

As briefly explained above, the `resolvers` define the code that is executed by the Lambda whenever an API call
is made. In the resolvers we verify the input of the API call and we call the corresponding Service where the business logic 
is defined. Resolvers should NOT include any business logic.

Each resolver receives the following parameters:

1. The `context` is provided by the GraphQL engine as an object with two properties
    - `context.engine` : a db.Engine instance (the database connection)
    - `context.username` : the username performing the api call
2. The `source` parameter is optional. If  provided, it holds the result of the parent field
3. `**kwargs` are the named field parameters

For example, let's see the dataset creation resolver (`modules.dataset.api.resolvers.py`):
```
def create_dataset(context: Context, source, input=None):
    RequestValidator.validate_creation_request(input)

    admin_group = input['SamlAdminGroupName']
    uri = input['environmentUri']
    return DatasetService.create_dataset(uri=uri, admin_group=admin_group, data=input)
```

As you can verify, in the resolvers we do not include any business logic, we only verify the input and call the corresponding
module service.

#### services
Here is where the business logic of the module API calls is defined. There are 2 types of files in this directory:
- One `<MODULE_NAME>_permissions.py` file that defines the application permissions that apply to the module.
- One or more `<MODULE_NAME>_<SUBCOMPONENT>_service.py` files that define all the application logic related to the module subcomponent. Like 
calling the `db` repositories, triggering `handlers` with the WorkerHandler or `cdk` stack deployments with the stack helper.

**Permissions** 

With the permissions checkers implemented in `core.permissions` and in `core.environment.env_permission_checker.py`, 
if a service function is decorated, data.all checks the permission
of the user before executing the action. For example, in the `create_dataset` function of the `DatasetService`, 
we take the user and check whether it has tenant permissions to MANAGE_DATASETS, has resource permissions on the 
environment resource to CREATE_DATASET or if the user groups have permissions to CREATE_DATASET in that environment.

```
@staticmethod
    @has_tenant_permission(MANAGE_DATASETS)
    @has_resource_permission(CREATE_DATASET)
    @has_group_permission(CREATE_DATASET)
    def create_dataset(uri, admin_group, data: dict):
      .....
```
Each of these decorators refer to a different type of permission:
- `TENANT_PERMISSIONS` - Granted to the Tenant group. For each resource we should define a corresponding MANAGE_<RESOURCE> permission
- `ENVIRONMENT_PERMISSIONS` - Granted to any group in an environment. For each resource we should define a list of actions regarding that resource that are executed on the environment (e.g. List resources X in an environment)
- `RESOURCE_PERMISSION` - Granted to any group. For each resource we should define a list of all actions that can be done on the resource. We also need to add the permissions for the Environment resource (ENVIRONMENT_PERMISSIONS)

If a function is decorated with permission checker decorators, it should pass `uri` and `admin_group` as parameters. They
are needed to validate the permissions of the user in relation to the groups and resources.

When creating a new resource that has associated permissions, the corresponding RESOURCE_PERMISSIONS should be attached.
You can take the example for dataset creation as a reference.

```
    ResourcePolicy.attach_resource_policy(
        session=session,
        group=environment.SamlGroupName,
        permissions=DATASET_ALL,
        resource_uri=dataset.datasetUri,
        resource_type=Dataset.__name__,
    )
```


#### ModuleInterfaces in __init__.py
Core and module code is executed in different compute components of the architecture of data.all. All backend code is 
executed in AWS Lambdas (GraphQL Lambda, Worker Lambda, ESProxy Lambda) or in 
ECS Fargate tasks on demand (CDKProxy task and Share task) or scheduled (Stack updates, Catalog Syncer).


If a module is active, the module code needs to be imported to the corresponding compute component so that it can be executed.
To import the necessary code into each of the compute components, we will use the `ModuleInterface` ABC class defined in `base.loader.py`.

![](img/HLD-backend-data.allV2.drawio.png#zoom#shadow)


In the `__init__` file of each of the modules we will declare a `ModuleInterface` class for each compute component that
needs to run module code. We need to define the abstract class method `is_supported`
returning the `ImportMode` that the particular `ModuleInterface` is interacting with.


There are 5 types of `ImportMode` (imported from `base.loader.py`) 
depending on the different infrastructure components that import module code.
- API - GraphQL API Lambda
- CDK - CDK Proxy
- HANDLERS - AWS Worker Lambda
- STACK_UPDATER_TASK - ECS Task that updates CDK stacks
- CATALOG_INDEXER_TASK - ECS Task that updates items indexed in the Catalog

**Note**: if you want to add a new `ImportMode` class, you'll need to define the new import mode and use the 
`loader` base functions in your compute component. In the `backend/api_handler.py` you can see one example. Pay
attention to the `load_modules` function.

```
load_modules(modes={ImportMode.API})
```

For a deeper dive - let's look at the following example from `modules.mlstudio`:

`MLStudioApiModuleInterface` is a class
that inherits `ModuleInterface`. `is_supported` returns `ImportMode.API` which means that the interface 
will import code into the GraphQL API Lambda. 

Since we want the GraphQL API Lambda to execute module code, we will import `dataall.modules.mlstudio.api` and other 
API related sub-packages when the interface class is initialized. 

In the sections below, we will dive deep
into the typical sub-packages for each ImportMode, but for the loading just remember: interface to import module code
in each of the compute components.

```
class MLStudioApiModuleInterface(ModuleInterface):
    """Implements ModuleInterface for MLStudio GraphQl lambda"""

    @classmethod
    def is_supported(cls, modes):
        return ImportMode.API in modes

    def __init__(self):
        import dataall.modules.mlstudio.api
        from dataall.modules.mlstudio.services.mlstudio_permissions import GET_SGMSTUDIO_USER, UPDATE_SGMSTUDIO_USER
        TargetType("mlstudio", GET_SGMSTUDIO_USER, UPDATE_SGMSTUDIO_USER)

        log.info("API of sagemaker mlstudio has been imported")
```


## frontend/ <a name="frontend"></a>
The frontend part of this project is developed using React.js and bootstrapped using [Create React App](https://github.com/facebook/create-react-app). You can run the app in development mode using `yarn start`, and open [http://localhost:8080](http://localhost:8080) to view it in the browser.

Overview of the frontend directory:
```
frontend/
├── docker/
├──── dev/
├────── Dockerfile : contains the docker config for the dev environment
├────── nginx.config : contains the nginx config for the dev environment
├──── prod/
├────── Dockerfile : contains the docker config for the prod environment 
├────── nginx.config : contains the nginx config for the prod environment
├── public/ : contains static files such as index.html and icons like the app logo and favicon
├── src/ : contains the major components of the frontend code, to be discussed in detail in the src/ section below
└── jsconfig.json : used to reference the root folder and map aliases/modules to their respective paths relative to the root folder.
```

### src/ <a name="src"></a>
This section contains the major components of the frontend code. Here is a short description of all the components of the src folder, we will deep dive subsequently on the contents of each module.

```
src/
├── authentication/ : contains files, contexts, hooks related to user and guest authentication
├── design/ : contains scripts related to the ui design of the app, layout and theme settings
├── globalErrors/ : global error reducers, uses redux
├── modules/ : contains directories of each view/screen in the app with their related components, hooks and services
├── services/ : contains common graphql schemas and hooks used to call the backend APIs which are then plugged into the frontend
├── utils/ : common helpers used across the app
├── App.js - entry point into the project, wrapped with the theme provider
├── index.js - react.js index script, wrapped with several providers
└── routes.js - where all routes and their hierachies are configured
```
#### authentication/ <a name="authentication"></a>
In this section, we handle the user and guest authentication logic and views for the application. The directory contains React `contexts`, `hooks`, `components` and `views` used to handle local and production environment authentication. 

```
autentication/
├── components/
├── contexts/
├── hooks/
├── views/
└── index.js
```

We used React Context API to handle the authentication state mangagement. `CognitoAuthContext.js` handles the AWS deployment and `LocalAuthContext.js` for local deployment.
Then `AWS Amplify` is used to connect the app to `AWS Cognito` for production auth and a default anonymous user  is set for local environment.

The `useAuth` hook is used to decide the auth context to use depending on the deployment environment, and `AuthGuard` is a wrapper to verify authentication before routing users to the requested pages in the application.

To create a user for your production deployment, follow these steps:
 - Login to your AWS deployment account, then create a user pool in `AWS Cognito`.
 - Add a user to the user group and attach the user to a user group
 - Use the credentials to login to `data.all`, you will be asked to change your password on the first login.


#### design/ <a name="design"></a>
This section contains script relating to the UI design of the frontend, including theming and theme settings, layout, icons, design components and logic. 

```
design/
├── components/
├── contexts/
├── hooks/
├── icons/
├── theme/
└── index.js
```

There are two themes, `DARK` and `LIGHT` and their basic settings can be found in the `theme/` directory.
We used React Context API to handle theme settings in `SettingsContext.js`, the default theme is set to match the browser's prefered color scheme or `DARK` if no color scheme is set.  

Common hooks used in the UI design like `useCardStyle` (default card component styling), `useScrollReset` (scroll to the top of the page) are in the `hooks` directory. 

#### globalErrors/ <a name="globalErrors"></a>
In this section, we used Redux to handle global error notifications. Error actions that are dispatched across the application are handled by the `errorReducer.js` which are then displayed in the `ErrorNotification.js` snackbar.

#### modules/ <a name="modules"></a>
The modules folder is one of the most important folder in the `src/` directory. It contains distinctive logically related views, services and hooks of `data.all` features that we have sectioned into modules.

##### Overview of the modules directory:
```
modules/
├── Administration/
├── Catalog/
├── Dashboards/
├── Datasets/
├── ...
├── MLStudio/
├── Shared/
└── constants.js
```
Each module folder contains components, hooks, services and pages related to a view (screen) in the application. 
The `components`, `hooks`, and `services` directories contain only their respective parts of the code **that are only used** inside each module. The `views` folder contains the screens or pages in the module. 

##### Structure of a module: <a name="structure_of_a_module"></a>
```
ModuleName/
├── components/ : contains all components (a singular section of a view) used only in module
├──── ModuleComponentA.js
├──── ModuleComponentB.js
├──── index.js
├── hooks/ : contains all hooks used only in the module
├──── useSomethingA.js
├──── useSomethingB.js
├──── index.js
├── services/ : all graphql schema code used only in the module
├──── someServiceA.js
├──── someServiceB.js
├──── index.js
├── views/ : all views/pages belonging to the module 
├──── ModuleViewA.js
└──── ModuleViewA.js
```

As shown above, each directory in a module except the `views` folder must contain an `index.js` file that exports the directory's content. This is to simplify importing different parts of the code, and also to keep implementation details and internal structure of each directory hidden from its consumers.

##### The `Shared` Module: <a name="shared"></a> 
When working with React projects, often times we have components that are shared across multiple views and among other components.

The shared module contains components that are shared among multiple views in the frontend. Related components are then grouped together in folders and with an `index.js` file that exports the directory's content.

##### Adding a new module:
To add a new module please follow the following steps:
- Create a new directory for the new module under `src/modules`
- The module structure should follow the same structure mentioned above in the [**structure of a module**](#structure_of_a_module) section
- Mainly the module should be based around its views (or screens) so there must be a views directory
- All of (components, hooks, services) should be under their respective directory in the module
- Add the new module screens with their related URLs ot src/routes.js
- In case they need to use a (component, hook, service) from another module, then that part need to be refactored and moved into the **Shared** directory for shared components, and (authentication, design, globalErrors, ...) folders depending on its purpose.
- Any utils or helper should be under `src/utils` unless it's a helper that is super specific to this module, then it can be in the same directory as the module under helpers or utils.
- Lastly, remember all directories in a module except the views folder must have an `index.js` file that exports it's content.

#### services/ <a name="services"></a>
The services directory contains API calls, hooks and graphql schemas used to call the backend APIs. 

`services/graphql/` directory contains commonly used graphql api definitions sectioned into modules. These APIs are used globally across different modules and that is why they are not under their modules' directories.

For example, the `getDataset` mutation defined in the backend `data.api` package is used in several modules in the frontend code. So it is added to the global graphQL folder. 

We use Apollo Client and its `gql` package to parse GraphQL queries and mutations. Here, the mutation requires an input string of the `datasetUri` and returns a dataset object with the requested values.
```
export const getDataset = (datasetUri) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query GetDataset($datasetUri: String!) {
      getDataset(datasetUri: $datasetUri) {
        datasetUri
        owner
        description
        label
        name
        region
        ...
        statistics {
          tables
          locations
          upvotes
        }
      }
    }
  `
});

```

Inside the `services/hooks/` folder, we initialize `ApolloClient` in `useClient.js` and `useGroups.js` handles scripts to obtain Cognito or SAML user groups for the authenticated user.


#### utils/ <a name="utils"></a>
This directory contains common utility helper methods and constants used across the application. 

For instance, `moduleUtils.js` file handles the logic to activate or deactivate a module in the frontend, you can configure a module's visibility status in the root `config.js` file. 

Some modules visibility depends on others, for example, `Glossary` and `Catalog` modules are disabled when `Datasets` or `Dashboards` modules are disabled.

New utilility methods or helpers should be under here unless it's a helper that is super specific to a module, then it can be in the same directory as the module under `helpers` or `utils` folder.

### jsconfig.json <a name="jsconfig"></a>
The `jsconfig.json` file is used to configure aliases and React.js absolute imports. It reference the root folder (`baseUrl`) and map aliases or modules names to their respective paths relative to the root folder.
```
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "authentication/*": ["src/authentication/*"],
      "design/*": ["src/design/*"],
      "globalErrors/*": ["src/globalErrors/*"],
      "modules/*": ["src/modules/*"],
      "services/*": ["src/services/*"],
      "utils/*": ["src/utils/*"],
      "Shared/*": ["src/modules/Shared/*"]
    }
  }
}
```
**Please note:** New aliases must be added to the `jsconfig.json` file and mapped to their respective paths in order to be used.

## tests/ <a name="tests"></a>
`pytest` is the testing framework used by data.all.
Developers can test the GraphQL API directly, as data.all can run as a local Flask app. 
API tests are found in the tests/api package.

The pytest fixtures found in conftest.py starts a local development Flask server that exposes the 
GraphQL API. Tests can use the graphql_client fixture as a parameter to run queries 
and mutations against the local web server.

```
def test_get_dataset_as_owner(dataset, graphql_client):
    duri = dataset.datasetUri
    res = graphql_client.query(
        """
        getDataset(datasetUri:"%(duri)s"){
            datasetUri
            label
            description
            tags
            userRoleForDataset
        }
    """
        % vars()
    )
    print (res)
    assert res.data.getDataset.datasetUri == duri
    assert res.data.getDataset.userRoleForDataset == DatasetRole.Owner.name


```

## compose/ <a name="compose"></a>
It contains the elements used by docker compose to deploy data.all locally. The application is containerized in
5 containers that are orchestrated with docker-compose. 
- frontend
- graphql
- db
- cdkproxy
- esproxy

Check [Deploy locally](./deploy-locally/) if you want to use this feature and run data.all locally.

## documentation/ <a name="userguide"></a>
This folder contains information for developers to add content to the user guide documentation accessible from the UI.
Here you can customize the documentation that is linked to the user guide domain. We are using [MkDocs](https://www.mkdocs.org/)
package to generate the site.

**Work locally** 

If you already have a virtualenv for the data.all project and
you have activated the virtualenv shell, simply cd into the documentation/userguide folder and run the following. 
The last command will run a local mkdocs server running on port 8000.

```bash
> cd documentation/userguide
> pip install -r requirements.txt
> mkdocs serve

```


