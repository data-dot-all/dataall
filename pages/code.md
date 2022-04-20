---
layout: default
homePage: false
title: Code Walkthrough
permalink: /code/
---
# **Code Walkthrough**

The data.all package is a mono-repo comprising several sections:

- [deploy/](#deploy)
- [backend/](#backend)
- [frontend/](#frontend)
- [tests/](#tests)
- [documentation/](#userguide)

## deploy/ <a name="deploy"></a>
We deploy the data.all tooling, backend and frontend using AWS Cloud Development Kit, which offers
high level abstractions to create AWS resources.

The deploy folder is a CDK application, with an `app.py` deploying a CI/CD stack. In the final deploy step of the
[Deploy to AWS](./deploy-aws/) guide, we are deploying the CI/CD pipeline stack defined in this section.


### stacks
As explained above, here is the code that defines the CI/CD pipeline in the tooling account. More specifically,
the `PipelineStack` is defined in `stacks/pipeline.py` 


From this stack, we deploy a CodePipeline pipeline and other stacks as standalone resources (e.g. `VpcStack` from `stacks/vpc.py`).
In addition, we define some CodePipeline deployment stages such as the stage that deploys 
the backend code `BackendStage` from `stacks/backend_stage`.

In the pipeline stack `PipelineStack` we deploy the following, which deploy the sub-stacks:
- `AlbFrontStage`
  - `AlbFrontStack`: Application Load Balancer for the UI applications
- `CloudfrontStage`
  - `CloudFrontStack`:
- `BackendStage`
  - `BackendStack`: 
    - `AuroraServerlessStack`: Aurora RDS Database and associated resources - data.all objects metadata
    - `IdpStack`: Cognito and IdP stack
    - `ContainerStack`: ECS stack
    - `CloudWatchCanariesStack` if enable_cw_canaries=true
    - `CloudWatchRumStack` if enable_cw_run=true
    - `DBMigrationStack`: tool to migrate between Aurora versions of the database
    - `LambdaApiStack` : Lambda Function stack
    - `MonitoringStack` : CloudWatch alarms and monitoring resources
    - `OpenSearchStack`: OpenSearch cluster - data.all central catalog
    - `ParamStoreStack` : AWS SSM parameters
    - `S3ResourcesStack` : S3 resources
    - `SecretsManagerStack` : AWS SSM Secrets
    - `SqsStack` : SQS
    - `VpcStack`: VPC
- `AuroraServerlessStack`: Aurora RDS Database and associated resources - for integration testing
- `CodeArtifactStack`
- `ECRStage`
- `VpcStack`



There are other elements in the `deploy` folder:
```
deploy/
├── pivot_role/  : with the template for the data.all IAM Pivot Role 
├── configs/ : scripts that create configuration files for Cognito, CloudFront and CloudWatch RUM
├── custom_resources/ : resources or actions not included in CloudFormation
└── canaries/: scripts for canary used in Canary stack if CloudWatch canary is enabled
```

## backend/ <a name="backend"></a>
In this section we will touch upon the main components of the backend code. We will start with how do we communicate
with the Aurora database, then we will focus on the code run by each of the compute components:
API Handler Lambda, the Worker Lambda, the ECS Fargate Cluster and the OpenSearch Lambda. 

### dataall.db

The `dataall.db` package implements the database connection with our persistence layer.
It can work with a local postgresql instance or with an Aurora database instance.

The idea is that this package processes all requests to our database, it can be from the Lambda API Handler, Lambda Worker
or the ECS tasks. This is the package that handles all database operations regardless of the compute component.
The exports from this package are:

1. `aws.db.get_engine(envname='local')` : returns a wrapper for a SQLAlchemy  engine instance
2. `aws.db.Base` : a SQL alchemy Base metadata class
3. `aws.db.Resource` :  a SQL alchemy class that holds common fields (label, created,...) found in data.all models
4. `aws.db.create_schema_and_tables` :  a method that will create schema and tables

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


**Note**: Granular permissions specified from the UI are stored in the permission table. Check the permission model and
apis to dig deeper into the logic.


### dataall/api

The api is exposed using the [`ariadne` GraphQL package](https://ariadnegraphql.org/). 
The overall flow of GraphQL resolution is  found in the `app.py` module using
the [`graphqlsync`](https://ariadnegraphql.org/docs/0.4.0/api-reference#graphql_sync)  from `ariadne`.

The data.all `api` package is where the GraphQL API is defined. This is the Lambda that processes all API calls
made from the frontend. This folder contains 2 packages: 
- `gql`: package to support GraphQL schemas. It is used to programmatically define GraphQL constructs.
- `Objects`: contains the business logic of our application


Each GraphQL Type defined in the data.all GraphQL API has one package in the `api.Objects` package,
and each defines the following modules:

1. `schema.py` :  the definition of the schema
2. `mutations.py` : the definition of mutations for the GraphQL type
3. `queries.py` : the definition of queries for the GraphQL type
3. `input_types.py` : the definition on input types for the GraphQL type
4. `resolvers.py` : the actual code that *resolves* the fields

**Let's take an example** 

We perform one type (GraphQL type) of API calls referent to data.all environments. Hence,
we created an Object called "Environment" by adding a sub-directory with the above listed modules. 
In `schema.py` we defined the schema of the Environment, note that the results of
a subquery can be part of the schema. 

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


### dataall/aws

The `dataall.aws` package is where all the AWS logic is implemented. In other words, the code in the handlers serves 
as an interface with AWS services. 

```
handlers/:
├── cloudformation.py
├── cloudwatch.py
├── codecommit.py 
├── codepipeline.py
├── ecs.py
├── glue.py
├── parameter_store.py
├── quicksight.py
├── redshift.py
├── s3.py
├── sagemaker.py
├── sagemaker_studio.py
├── sns.py
├── sqs.py
├── stepfunction.py
└── sts.py ---> used to assume roles on different AWS accounts
```

These scripts define Python classes that can imported, for example by the API resolvers. Here is an example of
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
In addition, in `service_handlers.py` we defined the `WorkerHandler` class that does
not implement general interactions with AWS services. The Worker Lambda processes requests based on this class as you 
see in its code in `backend/aws_handler.py`. 


The `WorkerHandler` python class is in charge of
routing tasks to python functions.
This class has a singleton instance called `Worker` that has two apis:

1. `Worker.queue(engine, task_ids: [str]))` : an interface to send a list of task ids to the worker
2.  `Worker.process(engine, task_ids: [str])`: the actual work to process a list of tasks


Additionally, the `Worker` singleton exposes a decorator function to register handler functions.
For example, suppose you want to implement a handler for tasks with `{"action": "foo"}`.
The following code will register the `handle_foo` function as the handler for `foo` actions:
```python
from dataall.aws import Worker
from data.all import models

@Worker.handler(path="foo")
def handle_foo(engine, task: models.Task):
    pass

```

Any handler needs to have the same signature:
```python
from dataall import models
def handler(engine, task:models.Task):
    """ handler signature """
    pass
```
Any handler will receive two parameters:

1. `engine` :  an instance of `db.Engine`
2. `task` : an instance of a `models.Task`  record

The code in `dataall.api` will use the `Worker.queue` to queue tasks in the FIFO SQS queue **in order**.
The handler code in `dataall.aws` will receive tasks, read task data from the Database,
and assume a role in the AWS Account Id where the action needs to be performed

The AWS Lambda hosting this code receives JSON objects sent by the api layer.
The JSON object received represents a task, and has three keys:

1. `action`: the name of the action to be performed
2. `taskid` : the identified of the task as found in the `task` table
3. `payload` : any additional information associated with the task

### dataall/tasks

### dataall/cdkproxy

This package contains the code associated with the deployment of CDK stacks that correspond to data.all resources.
The code in this package consists of wrapping the `cdk` cli through a REST API interface.
in this package, you'll find a package called `stacks` that holds the
definition  of AWS resources associated with data.all high level abstractions (e.g. : Dataset).

The API itself consists of 4 actions/paths :

- GET / : is the server up ?
- POST /stack/{stackid} : create /update the stack
- DELETE /stack/{stackid} : deletes the stack
- GET /stack/{stackid] : returns stack status

The webserver is running on docker, using Python's  [FASTAPI](https://fastapi.tiangolo.com/) web framework and running using [uvicorn](https://www.uvicorn.org/) ASGI server.

When a data.all resource is created, the api sends an HTTP request to the docker service and the code runs the appropriate stack using cdk the cli.

!!! note
    Why  not Lambda ?
    The `cdk` cli  offers no programmatic interface at the moment, and stacks can take
    long minutes to run. Also, spawning subprocess in lambda is doable but not idea.



cdkproxy currently supports the following stacks defined as cdk stacks in the `cdkproxy.stacks` sub-package:

1. environment :  the environment stack bootstrap an AWS Account/ Region with resources and settings needed by data.all to operate on the account
2. dataset: the dataset stack creates and updates all resources associated with the dataset, especially resources related to data sharing
3. gluepipeline : the glue pipeline stack creates a CI/CD pipeline for data processing
4. shareobject :  the share object stack is handling the import of remote shared tables in an environment using Lakeformation cross account data sharing



### Diagram
```mermaid
sequenceDiagram
    participant A as data.all λ
    participant D as DB
    participant W as worker λ
    participant H as handler
    participant C as Target AWS Account
    A->>D : (1) write tasks to db
    D-->>A : (2)saved tasks
    A->>W: (3) send task messages through SQS
    W-->>D : (4)read tasks data from database
    W-->>H :(5) Routes task to handler
    H-->>C : (6) Assume role
    H-->>W : (7) STS Token
    H->>C :(8) performs AWS API Calls
    H->>W :(9) returns response
    W->>D: (10) updates task status


```



## frontend/ <a name="frontend"></a>


## tests/ <a name="tests"></a>
`pytest` is the testing framework used by data.all.
Developers can actually test the GraphQL API directly, as data.all can run as a local Flask app. 
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
Contains the elements used by docker compose that make possible to deploy data.all locally. 
Check [Deploy to AWS](./deploy-aws/) to see how.

## documentation/ <a name="userguide"></a>
This folder contains information for developers to add content to the user guide documentation accessible from the UI.
Here you can customize the documentation that is linked to the user guide domain. 

We are using MkDocs to generate the site, here is a [link](https://www.mkdocs.org/) to their official documentation.

**Work locally** 

If you already have a virtualenv for the data.all project and
you have activated the virtualenv shell, simply cd into the documentation/userguide folder and run:

```bash
> cd documentation/userguide
> pip install -r requirements.txt
> mkdocs serve

```

The last command will run a local mkdocs server running on port 8000.
