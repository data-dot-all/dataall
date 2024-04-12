

## About
`cdkproxy` is a package that exposes a REST API to run pre-defined
cloudformation stacks using the aws cdk package.

It is deployed as a docker container running on AWS ECS.

## How it works

cdkproxy exposes a REST API to manage pre-defined stacks.
It reads and updates tasks from the dataall database.
Somes APIs are run asynchrnously , returning an id for subsequent reads.
Some APIs are run synchronously.


Pre-defined cdk stacks are defined in the stack package.
To register a pre-defined stack, use the `@stack` decorator as in the example below  :

```python

from aws_cdk import (
    aws_s3 as s3,
    aws_sqs as sqs,
    core
)
from dataall.base.cdkproxy.stacks import stack

@stack(stack="mypredefinedstack")
class MyPredefinedStack(core.Stack):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)
        #constructs goes here

```


## Local setup

### pre requisites

1. You must have docker installed
2. You must have ~/.aws folder with your aws credentials

### build the image
At the root folder:
`docker build --network=host -t cdkproxy:latest . `

### Run the image
`docker run --network host -p 8080:8080 -v /home/moshir/.aws:/root/.aws:ro --name cdkproxy cdkproxy:latest `
