"""
Contains all submodules that can be plugged into the main functionality

How to migrate to a new module:
1) Create your python module
2) Create the following submodules:
    a) gql
    b) tasks
    3) cdk

    Even if your module doesn't use all the functionality these submodules needed
    for correct loading. There can be left  with just empty __init__.py
3) Define your module in config.json. The loader will use it to import your module

Remember that there should not be any references from outside to modules.
The rule is simple: modules can import the core/common code, but not the other way around
Otherwise your modules will be imported automatically.
You can add logging about the importing the module in __init.py to track unintentionally imports

Auto import of modules:
gql - contains the logic for processing GraphQL request. It registered itself automatically
see bootstrap() and @cache_instances

cdk - contains stacks that will be deployed to AWS then it's requested. Stacks will
register itself automatically if there is decorator @stack upon the class
see StackManagerFactory and @stack - for more information on stacks

tasks - contains code for short-running tasks that will be delegated to lambda
These task will automatically register themselves when there is @Worker.handler
upon the static! method.
see WorkerHandler - for more information on short-living tasks

Another example of auto import is service policies. If your module has a service policy
it will be automatically imported if it inherited from ServicePolicy

Manual import:
Permissions. Make sure you have added all permission to the core permissions
Permission resolvers in TargetType. see it for reference
"""
