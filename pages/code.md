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
  - [core/](#core)
  - [modules/](#core)
- [frontend/](#frontend)
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
    - `ContainerStack`: ECS stack
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
    - `VpcStack`: VPC
- `AuroraServerlessStack`: Aurora RDS Database and associated resources - for integration testing
- `CodeArtifactStack`: for our Docker Images
- `ECRStage`: for our Docker Images
- `VpcStack`



There are other elements in the `deploy` folder:
```
deploy/
├── pivot_role/  : with the template for the data.all IAM Pivot Role 
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
├── alembic.ini : used in migrations
├── api_handler.py : GraphQL Lambda handler
├── aws_handler.py : Worket Lambda handler
├── search_handler.py :  ESProxy Lambda handler
├── cdkproxymain.py : ECS CDK task
├── local_cdkapi_server.py : CDKProxy local server used in docker (replacing the cdkproxymain)
├── local_graphql_server.py : Graphql local server used in docker (replacing the api_handler)
├── requirements.txt : requirements file used in Docker images for Lambdas and local containers of the backend
```
Inside `dataall/` we have 3 main sub-packages:
- base - base code 
- core - components that are needed to operate data.all
- modules - components that can be configured or disabled
### base/ <a name="base"></a>

### core/ <a name="core"></a>

Core features:
``
activity
catalog
cognito_groups
environment
feed
notifications
organizations
permissions
stacks
tasks
vote
vpc
``
### modules/ <a name="modules"></a>

### dataall.db

The `dataall.db` package implements the database connection with our persistence layer.
It can work with a local postgresql instance or with an Aurora database instance.

The idea is that this package processes all requests to our database, it can be from the Lambda API Handler, Lambda Worker
or the ECS tasks. This is the package that handles all database operations regardless of the compute component.


The package has two modules:
- `models`: it defines the tables and their schemas in our Aurora RDS database.
- `api`: api calls against the RDS Aurora database.

API code relies on the popular Python's `sqlalchemy` ORM package. Here is an example of a query to count the tables
of an specific data.all dataset.
```
    @staticmethod
    def count_dataset_tables(session, dataset_uri):
        return (
            session.query(models.DatasetTable)
            .filter(models.DatasetTable.datasetUri == dataset_uri)
            .count()
        )
```

The exports from this package are:

1. `aws.db.get_engine(envname='local')` : returns a wrapper for a SQLAlchemy  engine instance
2. `aws.db.Base` : a SQL alchemy Base metadata class
3. `aws.db.Resource` :  a SQL alchemy class that holds common fields (label, created,...) found in data.all models
4. `aws.db.create_schema_and_tables` :  a method that will create schema and tables

**Note**: Granular permissions specified from the UI are stored in the permission table. Check the permission model and
apis to dig deeper into the logic.


### dataall/api

The api is exposed using the [`ariadne` GraphQL package](https://ariadnegraphql.org/). 
The overall flow of GraphQL resolution is  found in the `app.py` module using
the [`graphqlsync`](https://ariadnegraphql.org/docs/0.4.0/api-reference#graphql_sync)  from `ariadne`.

The data.all `api` package is where the GraphQL API is defined. This is the Lambda that processes all API calls
made from the frontend. This folder contains 2 packages: 
- `gql`: package to support GraphQL schemas. It is used to programmatically define GraphQL constructs.
- `Objects`: containing the business logic of our application.


Each GraphQL Type defined in the data.all GraphQL API has one package in the `api.Objects` package,
and each defines the following modules:

1. `schema.py` :  the definition of the schema
2. `mutations.py` : the definition of mutations for the GraphQL type
3. `queries.py` : the definition of queries for the GraphQL type
3. `input_types.py` : the definition on input types for the GraphQL type
4. `resolvers.py` : the actual code that *resolves* the fields

**Let's take an example** 

We perform one type (GraphQL type) of API calls referent to data.all environments. Hence,
we created an Object called "Environment" by adding a GraphQL Type with the above listed modules. 
In `schema.py` we defined the schema of the Environment. The schema can define fields from subqueries.

Now let's see how to add an API call for the creation of Environments. Since 
creating an environment is a mutation (it modifies the object), we added a MutationField in the `mutations.py` script with the 
`createEnvironment` API call and its expected input and output type. Here, we also referenced the "resolver" that we 
defined in the `resolvers.py` as the function `create_environment`.


You can directly check any of the Objects in the code, they follow this structure:

- `dataall.api.Objects.Foo.schema.py`

```python

from dataall.api import gql
from dataall.api.Objects.foo.resolvers import resolve_bar

Foo = gql.ObjectType(
    name="Foo",
    fields=[
        gql.Field(
            name="fooId",
            type=gql.NonNullableType(gql.ID)
        ),
        gql.Field(
            name="bar",
            type=gql.String,
            args=[
                gql.Argument(name="upper", type=gql.Boolean)
            ],
            resolver=resolve_bar
        )
    ]
)

```
- `dataall.api.Objects.Foo.queries.py`

```python

from dataall.api import gql
from dataall.api.Objects.foo.resolvers import get_foo

getFoo = gql.Field(
    name="getFooById",
    type=gql.Ref("Foo"),
    resolver=get_foo
)

```

- `dataall.api.Objects.Foo.resolvers.py`



```python
def resolve_bar(context, source,upper:bool=False):
    tmp = f"hello {context.username}"
    if upper:
        return tmp.upper()
    return tmp

def get_foo(context, source, fooId:str=None):
    return {"fooId" : fooId}

```

The parameters are defined as follows:

1. The `context` is provided by the GraphQL engine as an object with two properties
    - `context.engine` : a db.Engine instance (the database connection)
    - `context.username` : the username performing the api call
2. The `source` parameter is optional. If  provided, it holds the result of the parent field
3. `**kwargs` are the named field parameters

**Note**: If you are adding a new Object/GraphQL type, 
don't forget to add it in`backend/dataall/api/Objects/__init__.py`

### dataall/aws

The `dataall.aws` package is where all the AWS logic is implemented. It serves 
as an interface that performs API calls to AWS services. It has a unique folder containing:

```
handlers/:
├── cloudformation.py
├── cloudwatch.py
├── codecommit.py 
├── codepipeline.py
├── ecs.py ---------------------> Interface with ECS Fargate cluster
├── glue.py
├── parameter_store.py
├── quicksight.py
├── redshift.py
├── s3.py
├── sagemaker.py
├── sagemaker_studio.py
├── service_handlers.py ---------> Interface with Worker Lambda
├── sns.py
├── sqs.py
├── stepfunction.py
└── sts.py ---> used to assume roles on different AWS accounts
```

These scripts define Python classes that can imported (e.g. by the API resolvers in `dataall.api`). Here is an example of
the Dataset resolvers `backend/dataall/api/Objects/Dataset/resolvers.py` where we import
and use the class `Glue` to interact with AWS Glue:
```
def start_crawler(context: Context, source, datasetUri: str, input: dict = None):
    [.....]
        crawler = Glue.get_glue_crawler(
            {
                'crawler_name': dataset.GlueCrawlerName,
                'region': dataset.region,
                'accountid': dataset.AwsAccountId,
            }
        )
    [.....]
```
#### WorkerHandler
In `service_handlers.py` we defined the `WorkerHandler`  Python class.
Some resolvers might need to perform calls against AWS APIs. Most of the time, these API calls can be performed 
asynchronously, in which case, developers can use the `WorkerHandler` to send tasks that will be processed
asynchronously by the Worker Lambda function.
The `WorkerHandler`  is in charge of
routing tasks to the Worker AWS Lambda. 

This class has a singleton instance called `Worker` that has two apis:

1. `Worker.queue(engine, task_ids: [str]))`: an interface to send a list of task ids to the worker
2.  `Worker.process(engine, task_ids: [str])`: an interface to pick up and process a list of tasks


The `Worker` singleton exposes a decorator function to register handler functions that can 
be run by the worker. For example, for the Glue handlers (in `handlers/glue.py`), we want to define that the function 
`start_crawler` is run by the Worker Lambda. Therefore we use the decorator and define its path:

```
    @staticmethod
    @Worker.handler(path='glue.crawler.start')
    def start_crawler(engine, task: models.Task):
        with engine.scoped_session() as session:
            dataset: models.Dataset = db.api.Dataset.get_dataset_by_uri(
                session, task.targetUri
            )
            location = task.payload.get('location')
            return Glue.start_glue_crawler(
                {
                    'crawler_name': dataset.GlueCrawlerName,
                    'region': dataset.region,
                    'accountid': dataset.AwsAccountId,
                    'database': dataset.GlueDatabaseName,
                    'location': location,
                }
            )
```


The code in `dataall.api` will use the `Worker.queue` to queue tasks in the FIFO SQS queue **in order**. Tasks are 
defined first in the Aurora database and then we pass their unique identifier to the queue. In the example
below, taken from the same dataset resolver, we are queueing a `glue.crawler.start` action.

```
def start_crawler(context: Context, source, datasetUri: str, input: dict = None):
    [...]

        task = models.Task(
            targetUri=datasetUri,
            action='glue.crawler.start',
            payload={'location': location},
        )
        session.add(task)
        session.commit()

        Worker.queue(engine=context.engine, task_ids=[task.taskUri])
    [...]
```


The Worker AWS Lambda receives JSON objects with the task fields. Below is the code of the Worker Lambda defined in
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


The `WorkerHandler` in `dataall.aws` will then `process` the tasks: it reads task data from the Database, routes to 
the decorated handler function 
and assumes a role in the AWS Account where the action needs to be performed.

#### ECS
You might have overlooked the ECS interface. In the `dataall.aws` package we also define the connection to the
ECS Fargate cluster that performs long-running tasks. ECS `run_ecs_task` function connects with our cluster and
runs one of the tasks declared in the `dataall.tasks` package.

### dataall/tasks

In this package we define the long-running tasks executed by the ECS Fargate cluster:
- `bucket_policy_updater`: folder sharing by updating S3 bucket policies
- `catalog_indexer`: full indexing of all items from our persistence layer in the OpenSearch cluster
- `cdkproxy`: deployment of CDK stacks with `dataall/cdkproxy` package
- `share_manager`: table sharing operations
- `stacks_updater`: updates CDK stacks (support of cdkproxy)
- `tables_syncer`: syncs the tables between the Glue Catalog and the Aurora RDS database for our datasets.

### dataall/cdkproxy

This package contains the code associated with the deployment of CDK stacks that correspond to data.all resources.
`cdkproxy` is a package that exposes a REST API to run pre-defined
cloudformation stacks using AWS CDK.

**It is deployed as a docker container running on AWS ECS.**

When a data.all resource is created, the API sends an HTTP request 
to the docker service and the code runs the appropriate stack using `cdk` cli.

These stacks are deployed with the `cdk` cli wrapper
The API itself consists of 4 actions/paths :

- GET / : checks if the server is running
- POST /stack/{stackid} : creates or updates the stack
- DELETE /stack/{stackid} : deletes the stack
- GET /stack/{stackid] : returns stack status

The webserver is running on docker, using Python's  [FASTAPI](https://fastapi.tiangolo.com/) 
web framework and running using [uvicorn](https://www.uvicorn.org/) ASGI server.

The sub-package  `stacks` holds the
definition  of AWS resources associated with data.all high level abstractions. Currently, there are stacks for:

1. environment:  the environment stack with resources and settings needed for data.all teams to work on the linked AWS account.
2. dataset: the dataset stack creates and updates all resources associated with the dataset, included folder sharing bucket policies.
3. notebook: SageMaker Notebook resources
4. pipeline: CI/CD pipeline resources
5. redshift_cluster: Redshift stack
6. sagemakerstudio: SageMaker Studio user profile


To register a new type of stack, use the `@stack` decorator as in the example below  :

```python

from aws_cdk import (
    aws_s3 as s3,
    aws_sqs as sqs,
    core
)
from dataall.cdkproxy.stacks import stack

@stack(stack="mypredefinedstack")
class MyPredefinedStack(core.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        #constructs goes here

```

**Let's take an end-to-end example** 

In `data.api` dataset resolvers we have the GraphQL call to create a dataset:
```
def create_dataset(context: Context, source, input=None):
[...]
    stack_helper.deploy_dataset_stack(context, dataset)
    return dataset
```

Which uses the stack_helper from `Stack` GraphQL Type (`backend/dataall/api/Objects/Stack/stack_helper.py`) to queue or 
run the ECS task.
```
def deploy_stack(context, targetUri):
    [.....]
            if not Ecs.is_task_running(cluster_name, f'awsworker-{stack.stackUri}'):
                stack.EcsTaskArn = Ecs.run_cdkproxy_task(stack.stackUri)
            else:
                task: models.Task = models.Task(
                    action='ecs.cdkproxy.deploy', targetUri=stack.stackUri
                )
                session.add(task)
                session.commit()
                Worker.queue(engine=context.engine, task_ids=[task.taskUri])

        return stack
```
Remember, in the `dataall.aws` package is where we defined the interface with ECS and the `run_cdkproxy_task` function.
We are passing the task definition and the docker container to ECS which will use then the `dataall/cdkproxy` package
deployed in a docker container. The docker image is stored in ECR in the tooling account.


### dataall/searchproxy
The `dataall/searchproxy` package manages all operations with the OpenSearch cluster. Similarly to `dataall/db`, this
package implements the connection with the OpenSearch cluster for all compute components: API handler Lambda, Worker Lambda
and ECS tasks.

## frontend/ <a name="frontend"></a>
The frontend code is a React App. In this section we will focus on the components specific to data.all, particularly
the `src` folder.

### contexts
We define React Contexts to define "global" props that affect many child components in the application. 
For example, we set the initial Theme as "dark". We also use Contexts to define Authorization parameters which
might come from Amplify or from our local setting. 

- Amplify Context
- Local Context
- Settings Context

### hooks
Hooks are an addition to React 16.8. As they say in the docs: 
*"Hooks are functions that let you hook into React state and lifecycle features 
from function components."*  With hooks we can share
the same stateful logic across different components. 
Careful, Hooks are a way to reuse stateful logic but not the state itself.


We use some React hooks such as useState, useEffect and useCallback in our UI views. In addition, we also define
some custom hooks in the `hooks` folder:

```
hooks/:
├── useAuth: useContext on the context defined in contexts
├── useCardStyle
├── useClient: initialize Apollo Client (see below)
├── useGroups: obtain Cognito or SAML groups for the user
├── useScrollReset
├── useSettings
└── useToken: for Searches in Catalog
```

We use Apollo Client library to manage GraphQL data. Apollo Client's built-in React support allows you to 
fetch data from your GraphQL server and use it in building complex and reactive UIs using the React framework. 
Inside `hooks`, in `useClient` we initialize `ApolloClient`.

### api
This folder contains the GraphQL API definitions for each of our GraphQL Types.


Taking the example of the `createDataset` mutation defined in the backend `data.api` package, now
in the frontend code we use Apollo Client and its `gql` package to parse GraphQL queries and mutations. Here, the
mutation requires an input of the form `NewDatasetInput` as defined in the dataset `input_types` script in the 
backend `dataall.api` package. The mutation will return the `datasetUri`, `label` and `userRoleForDataset`.
```
import { gql } from 'apollo-boost';

const createDataset = (input) => {
  console.log('rcv', input);
  return {
    variables: {
      input
    },
    mutation: gql`
      mutation CreateDataset($input: NewDatasetInput) {
        createDataset(input: $input) {
          datasetUri
          label
          userRoleForDataset
        }
      }
    `
  };
};

export default createDataset;

```

### views
Contains each of the UI views. Each data.all component (e.g. Dataset, Environment) has its own subfolder 
of views. There are views that apply to multiple components. For example, we use the Stack views
in several tabs of our components. 

Inside the views we use hooks from `hooks` and call the GraphQL APIs defined in `api`. 

### components, theme and icons
Auxiliary UI resources used in views:
- components: default values (e.g. for filters), layouts, popovers...
- theme: dark or light theme
- icons


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


