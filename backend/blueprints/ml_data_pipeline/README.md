# Blue Print for Step Function based Data/ML Projects
The content of the directory is the directory that is used as a base for data.all Data/ML Projects. Upon creation of the project, the content of this directory is copied from central place in data.all to the business
account repository.

## Config.yaml
The resources supported by data.all and defined under aws_resources are:
- dynamodb for DynamoDB table
- apigateway for APIGateway
- sns_topic for SNS topic (including access policy)
- athena_workgroup for Athena Workgroups
- athena_prepare_statement for prepared SQL statements
- lambda_layer for Lambda layer
- lambda_function for a lambda function outside the main step function of the pipeline.
- batch_compute_environment, for AWS Batch Compute Environment
- batch_job_queue for AWS Batch Job Queue
- batch_job_definition for Batch Job Definition
- glue_connection for AWS Glue connection
- sagemaker_model_package_group for sagamaker model package group.


Under groups, we can define different types of steps:
- glue_job, for glue job
- athena_query, for athena query
- lambda_function, for creation of lambda function
- batch, for AWS Batch job
- sns_publish, for publishing a message to an SNS topic
- sagemaker_training, for SageMaker training
- sagemaker_hpo, for hyperparameter optimization using SageMaker
- sagemaker_processing, for SageMaker processing
- sagemaker_batch_transform, for Sagemaker batch transform
- sagemaker_model, for creation of a SageMaker model
- sagemaker_endpoint_config, for creation of an SageMaker endpoint configuration
- sagemaker_endpoint, for creation of SageMaker endpoint
- choice, for a simple, typically runtime branching.

Check the example provided below with examples for all the types of steps.
### Retry and failure handling
Adding the following code at the end of the config.yaml will add retry and catch behavior.
```
retry:
  error_equals:
  - States.ALL
  interval_seconds: 60
  retry_attempts: 3
  backoff_rate: 2
catch:
  error_equals:
  - States.ALL
  result_path: $
  groups:
  - name: SNS_publish_failure
    jobs:
    - name: '{{model_name}}_sns_publish_failure'
      type: sns_publish
      config:
        topic_name: '{{model_name}}'
        message: '{{model_name}} failed'
```
### Variables
- environment variables: the following key-value variables can be directly referenced as {{key}} in the general config.yaml:
  1. stage
  2. aws_account_id
  3. aws_region
  4. pipeline_name
  5. pipeline_bucket
  6. saml_group
  7. environment_role_arn
  8. sns_topic_arn

- variables.yaml file: any key-value variable defined in this file can be referenced as {{key}} in the config.yaml (see examples below)
```
model_name: example
```
- on-runtime variables (e.g. from the triggering lambda that receives an event as trigger) can be referenced as $.variable_name
### if-clauses
Based on variables you can define conditions. For example in a lambda layer:
```
  - name: numpy_layer
    type: lambda_layer
    config:
        layer_arn:
                arn: {% if aws_region == 'eu-central-1' %}
                        "arn:aws:lambda:eu-central-1:292169987271:layer:AWSLambda-Python37-SciPy1x:35"
                     {% elif aws_region == 'eu-west-1' %}
                        "arn:aws:lambda:eu-central-1:399891621064:layer:AWSLambda-Python37-SciPy1x:37"
                     {% endif %}
                id: "scipynumpy"
```
## customcode: files that you have to modify
Based on the config.yaml resources and steps multiple files have to be added/modified in the customcode folder, namely:
- lambda_functions: to define the lambda functions used in the pipeline.
- lambda_layers: to define the lambda layer to be used.
- sagemaker_jobs: to write sagemaker jobs
- glue_jobs: to define the configuration of the glue jobs
    queries: to define sql queries executed by the query glue handler
    pydeequ: code to apply in the profiling glue handler
    variables_files: variable files to be read and rendered in the different glue yaml files
    *note that additional handlers are defined in the engines folder (see README inside customcode/glue)
- athena_jobs: to define the configuration of Athena queries
    athena_queries: to store the sql statements to be executed by Athena
- batch: to store the code for the specific batch jobs


## engines: integration with resources
The integration with the different resources is done in the engines folder.
data.all data pipeline opens completely for modification. Engines can be modified in the repository at the project level.
- lambda
- glue
- sagemaker
- athena
- batch
- apigateway
- dynamodb
- sns
In the resource_task.py there are some additional definitions for several related resources. In addition, the directory utils contains the methods and classes necessary to build the pipeline and its resources.
Additional engines or  new step types require modifications in these scripts.

## Examples
Contains sample data and config.yaml and customcode examples. Includes the default example that is created in the first commit.

## Tests
Correspond with the unit tests executed in the RunTests stage in the CodePipeline pipeline.

```
- python -m pytest --cov=engine --cov=utils --cov-branch --cov-report
  term-missing --cov-report xml:tests/unittests/test-reports/coverage.xml  --junitxml=tests/unittests/test-reports/junit.xml  tests/unittests
- python -m pytest --cov=lambdafx --cov=smjobs --cov-branch  --cov-report term-missing
  --cov-report xml:tests/unittests-custom/test-reports-custom/coverage.xml  --junitxml=tests/unittests-custom/test-reports-custom/junit.xml  tests/unittests-custom
```
- unittests: unit tests for the stack, stack utils and engines. the tests/customcode folder and config_files are auxiliar resources for these tests.
- unittests-custom: unit tests for the customcode executed in the step function. Currently there is an example corresponding to the lambda default step function


## Example of a config.yaml with all types of resources
The purpose of this example is to provide an example of the configuration of the resources, it does not represent a real example
For Batch, Athena and Glue refer to the README files in customcode/batch, /athena and /glue correspondingly.

```yaml
# An example YAML file with all types of steps
name : Dummy pipeline
comment: dummy pipeline that won't work

aws_resources:
  # Contains the definition of resources needed by the pipeline that are not part of the step function.
  # Currently supported resources are:
  # Dynamo DB table, API Gateway, Lambda function, Lambda Layer, Athena Workgroup, Athena prepared statement, Glue connection and SNS topic including policy

  ## LAMBDA LAYER
  # There are 3 ways of defining lambda layers:
  # 1. executing a terminal command : like the pandas_layer (from requirements.txt) and the py_commons_layer (from Python class, see dpc example)
  # Also, the type for this type can be "simple" or "custom"
  # For simple:It contains requirements.txt file or files corresponding to a layer.
  # For custom: # A layer that needs some post processing (e.g. removal of some files).
  # 2. from public arn: like numpy_layer(careful, this arn change with the AWS region)
  # 3. from zip in S3 bucket: like wrangler_layer (Note that some layers are available in public s3 buckets)

  - name: pandas_layer
    type: lambda_layer
    config:
       layer_entry: "customcode/lambda_layers/pandas_sklearn"
       bundle_type: custom
       cmd: "rm -rf /asset-output/python  && pip install -r requirements.txt --target /asset-output/python --quiet &&  rm -rf /asset-output/python/scipy* && rm -rf /asset-output/python/numpy*"

  - name: py_commons_layer
    type: lambda_layer
    config:
      layer_entry: "customcode/lambda_layers/py_commons"
      bundle_type: custom
      cmd: "rm -rf /asset-output/python  && mkdir -p /asset-output/python/py_commons && cp * /asset-output/python/py_commons"

  - name: numpy_layer
    type: lambda_layer
    config:
        layer_arn:
                arn: "arn:aws:lambda:eu-central-1:111111111111:layer:AWSLambda-Python37-SciPy1x:35"
                id: "scipynumpy"

  - name: wrangler_layer
    type: lambda_layer
    config:
      bucket_arn: "arn:aws:s3:::<<INTRODUCE HERE YOUR BUCKET, OR OPEN BUCKET>>"
      key: "awswrangler/awswrangler-layer-2.9.0-py3.8.zip"
      runtime: "python3.8"

  ## GLUE CONNECTION
  - name: redshift_connection
    type: glueconnection
    config:
       subnet_id: subnet-xxx
       security_group_id:
           - sg-xxx
       jdbc_url: /glueconnection/jdbc_url
       username: /glueconnection/username
       password: /glueconnection/pass

  ## SNS TOPIC
  # By default all principals from the account can publish and subscribe to the sns topic
  - name: MySNSTopicName # it creates an sns topic with this name
    type: sns_topic
    config: #Introduce the SUBSCRIPTION accounts that will have subscribe access to the topic.
        subscriber_accounts: ["2222222222..","111111111111..."]

  ## BATCH COMPUTE ENVIRONMENT
  - name: MyBatchComputeEnvironment
    type: batch_compute_environment
    properties:
       compute_resource_type: SPOT
       bid_percentage: 100
       subnet_from_cloudformation: "vpc-public-cf-SubnetTier2List"
       vpc_from_cloudformation: "vpc-public-cf-VpcId"

  ## BATCH JOB QUEUE
  - name: MyBatchJobQueue
    type: batch_job_queue
    properties:
      compute_environment:
         compute_environment_ref:
            - MyBatchComputeEnvironment

  ## BATCH JOB DEFINITION
  - name: MyBatchJobDefinition
    type: batch_job_definition
    job_definition:
         container_properties:
           image:
             assets:
              directory: customcode/batch/Example
              file: Dockerfile

  ## ATHENA WORKGROUP
  - name: MyAthenaWGName
    type: athena_workgroup
    comment: "optional string"
    config:
      query_result_location: "s3://bucketname/prefix/"

  ## ATHENA PREPARED STATEMENTS
  - name: MyPreparedStatement
    type: athena_prepared_statement
    comment: "optional string"
    config:
      query:
        query_string: SELECT * FROM "{{model_name}}"."table" where "var1"=? and "var2"=?
      workgroup: primary
      variables:
        model_name:{{model_name}}

  - name: MyPreparedStatementFromFile
    type: athena_prepared_statement
    comment: "optional string"
    config:
      query:
        file: "customcode/..../file.sql"
      workgroup: primary

  ## API GATEWAY
  - name: MyApiGateway
    type: apigateway
    comment: "optional string"


  ## DYNAMODB
  - name: MyDynamoDBTable
    type: dynamodb
    comment: "optional string"
    config:
      read_capacity: 5
      write_capacity: 5
      partition_key:
        name: "region"
        type: "string" #"number", "binary" or "string"
      sort_key:
        name: "another"
        type: "number" #"number", "binary" or "string"


  ## lAMBDA FUNCTION
  # Same as the lambda functions in groups

  ## SAGEMAKER MODEL PACKAGE


# Schedulers and triggers
properties:
 schedulers:
  - cron: "cron(0 22 * * ? *)"

triggers:
# Contains an optional lambda function that triggers the step function
# With this we can define the input of the step function
# Optionally: It can be subscribed to an SNS topic and messages to that topic would start the trigger and serve as event.
# Optionally: the trigger can be scheduled with a cron job
   - name: MyTriggerName
     type: lambda_function
     config:
       entry: "customcode/lambda_functions/sfn_trigger"
       index: "handler.py"
       handler: "handler"
       sns: #optional
           topic_arn: "topic_arn"
      schedulers: #optional
        - cron: "cron(0 4 * * ? *)"
          payload: "{'secret': 'somesecret', 'bucket': 'datasetbucket'}"
        - cron: "cron(0 5 * * ? *)"
          payload: "{'secret': 'somesecret', 'bucket': 'datasetbucket'}"


groups:
# Contains the definition of the step function and its steps
# each group is executed in sequence after the previous group
# all jobs inside a group are executed in parallel

  - name: Step1WithLambdaAndGlue
    jobs:
      ## LAMBDA FUNCTION
      - name: MyLambda
        description: "describing it"
        type: lambda_function
        config:
          entry: "customcode/lambda_functions/example_fx"
          index: "example_handler.py"
          handler: "handler"
          runtime: "python3.7"
          layer_ref:
             - pandas_layer
             - numpy_layer
          timeout: 300

      ## GLUE JOBS
      # Glue jobs can be configured using pre-existing handlers or from scratch
      # For using a handler we define a yaml file as follows:
      - name : MyGlueJob
        config: "customcode/glue/glue_jobs/example.yaml" # it configures the glue job
        type: glue_job

  - name: Step2WithAthena
    jobs:
      ## ATHENA QUERIES
      - name: MyAthenaFunction
        type: athena_query
        comment: "describe me please"
        config:
          config_file: "customcode/athena/athena_jobs/example.yaml" # it configures the athena job
          workgroup: MyAthenaWGName # we can reference the previously created workgroup
          # If no workgroup is assigned, then the environment-ADgroup workgroup is chosen by default
          retry: # Optional, if no retry parameters are assigned, no retry strategy is configured
            error_equals: ["Athena.AmazonAthenaException","Athena.TooManyRequestsException"]
            interval_seconds: 1
            retry_attempts: 5
            backoff_rate: 2
          variables: # we can pass variables and referenced variables
            dimension : classification
            model_name : {{model_name}}

      ## EXECUTE ATHENA PREPARED STATEMENT
      - name: MyAthenaExecutePreparedStatement
        type: athena_query
        comment: "Some description here"
        config:
          config_file: "customcode/athena/athena_jobs/example.yaml"
          variables: [ "$$.Execution.Id","$.InputVar" ]

  ## PUBLISH TO SNS
  # To publish to SNS topic we can sue a topic created in the aws resources or an external SNS topic in this AWS account
  - name: Step3WithSNS
    jobs:
      - name: MySNSPublishTask
        type: sns_publish
        config:
          topic_name: MySNSTopicName-{{pipeline_name}}-{{stage}} #created in the AWS resources
          message: "ALL FILES LOADED"

  ## BATCH JOBS
  - name: Step4WithBatch
    jobs:
      - name : MyBatchJob
        type: batch
        job_queue_ref: MyBatchJobQueue
        job_definition_ref: MyBatchJobDefinition
        config:
        command:
           - -b
           - dhdatabasename
           - -o
           - model
           - -d
           - somedirectorywithpics
           - --height
           - "120"
           - --width
           - "210"

  ## SAGEMAKER
  - name: Step5TrainingSageMaker
    jobs:
      - name: Training
        type: sagemaker_hpo
        ext_job_name: "$.model_name" #From trigger lambda
        config:
          resources:
              - name: sagemaker_hpo_resource
                instance_count: 1
                instance_type: "ml.m5.2xlarge"
                volume_size: 30
          strategy: Bayesian
          objective:
              type: Minimize
              metric: "validation:merror"

          resource_limits:
              nb_of_training_jobs: 40
              max_parallel_training_jobs: 4

          parameter_ranges:
              - name: "alpha"
                min_value: 0
                max_value: 100
                scaling_type: Auto
                type: continuous

              - name: "gamma"
                min_value : 0
                max_value: 5
                scaling_type: Auto
                type: continuous

              - name: "max_delta_step"
                min_value: 1
                max_value: 10
                scaling_type: Auto
                type: integer

              - name: "max_depth"
                min_value: 4
                max_value: 8
                type : integer


              - name: "num_round"
                min_value: 5
                max_value: 20
                type: integer

          static_hyperparameters:
              - name: num_class
                value: 3

          algorithm:
              name: xgboost
              version: "1.2-1"

          output_path_from_input : "$.training_output"
          training_input_from_path:
              content_type: "$.training_input.content_type"
              train_s3_uri:
                bucket : "$.training_input.train_s3_uri.bucket"
                prefix_key: "$.training_input.train_s3_uri.key_prefix"
              validation_s3_uri:
                bucket: "$.training_input.validation_s3_uri.bucket"
                prefix_key:  "$.training_input.validation_s3_uri.key_prefix"

          resource_ref: hpo_resource
          max_runtime: 40000
        retry:
           retry_attempt: 3
        hpo_result_path : "$.hpo_output"
        model:
          model_name_path: "$.model_name"

  - name: Step6PredictionSageMaker
    jobs:
        - name: "Predict on Test set"
          type: sagemaker_batch_transform
          config:
              model_name_path: "$.model_name"
              transform_input:
                 content_type: "text/csv"
                 s3_data_source:
                    s3_uri_from_path: $.s3_transform_input

              data_processing:
                input_filter: "$[1:]"
                join_source: "Input"
                output_filter: "$[0,-1]"

              transform_job_name_path: $.transform_job_name
              transform_output:
                 s3_output_path_from_path: $.s3_transform_output
              transform_resources:
                 instance_count: 1
                 instance_type: "ml.m5.2xlarge"

  - name: Step7LaunchModelEndpoint
    jobs:
        - name: "EndPointChoice"
          type: "choice"
          choices :
              - input: "$.launch_end_point"
                condition:
                    BooleanEquals: true
                groups:
                   - name: "Config End Point"
                     jobs:
                         - name : iris-endpoint-config
                           type: sagemaker_endpoint_config
                           endpoint: "$.EndPoint"
                           config:
                              instance_type: "c5.2xlarge"
                              model_name_path: "$.model_name"

                   - name: "Launch Endpoint"
                     jobs:
                        - name: iris-endpoint
                          endpoint: "$.EndPoint"
                          type: sagemaker_endpoint
                          config:
                              wait_for_completion: "false"
                              retry_count:  30

```

# Multiple stacks
config.yaml is the stack that is mandatory. In addition, additional stacks can be defined under configs directory.
