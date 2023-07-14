"""
Contains all submodules that can be plugged into the main functionality

How to migrate to a new module:
1) Create your python module
2) Create an implementation of ModuleInterface/s in __init__.py of your module
3) Define your module in config.json. The loader will use it to import your module

Remember that there should not be any references from outside to modules.
The rule is simple: modules can import the core code, but not the other way around
Otherwise your modules will be imported automatically.
You can add logging about the importing the module in __init__.py to track unintentionally imports

Auto import of modules:
api - contains the logic for processing GraphQL request. It registered itself automatically
see bootstrap() and @cache_instances

cdk - contains stacks that will be deployed to AWS then it's requested. Stacks will
register itself automatically if there is decorator @stack upon the class
see StackManagerFactory and @stack - for more information on stacks

handlers - contains code for long-running tasks that will be delegated to lambda
These task will automatically register themselves when there is @Worker.handler
upon the static! method.
see WorkerHandler - for more information on short-living tasks

Another example of auto import is service policies. If your module has a service policy
it will be automatically imported if it inherited from ServicePolicy or S3Policy

Any manual import should be done in __init__ file of the module in ModuleInterface
"""
