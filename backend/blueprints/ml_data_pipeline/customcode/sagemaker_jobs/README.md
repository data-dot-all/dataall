```yaml
# An example YAML file

name : sample
variables:
  dev:
    foo : bar
  prod:
    foo: foo

gluejobdir: glue_jobs

groups:
  - name: "Function"
    jobs:
      - name: Handlerfx
        type: lambdafx
        config:
          entry: "lambdafx/example_fx"
          index: "example_handler.py"
          handler: "handler"
          layer_entry: "lambdafx/example_fx/requirements.txt"
          payload:
              param: "first_param"

  - name: "Prepare"
    jobs:
      - name : job1
        type: glue
        config: job1.yaml

      - name : job2
        type: glue
        config: job2.yaml

  - name: "Process"
    jobs:
      - name : Processing
        type: processing
        main: "sagemaker_jobs/processing/processing_job.py"
        config:
          stopping_condition:
            max_runtime: 3600

  - name: "Train"
    jobs:
      - name: "Training Model"
        type: training
        main: sagemaker_jobs/training/training_job.py
        config:

            timeout: 3600
            algorithm_specification:
              metric_definitions:
                - name: "t1"
                  regex: "."
              training_image:
                image_uri: "123456789012.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job"
                training_input_mode: "FILE"

            input_data_config:
              -
                channel_name: "train"
                data_source:
                  s3_data_source:
                    s3_location:
                      bucket: "sagemaker-eu-west-1-123456789012"
                      key_prefix: "data"

            output_data_config:
              s3_output_location:
                bucket: "sagemaker-eu-west-1-123456789012"
                key_prefix: "data"

            hyperparameters:
              p1: "3.8"
              p2: "E"

            resource_config:
              instance_count: 1
              instance_type: "m4.xlarge"
              volume_size: 35

            vpc_config:
                vpc_id: "vpc-0f63e205b5c888858"
                subnets:
                    -
                      "subnet-0ee1e02177e5fbbb8"

            stopping_condition:
              max_runtime: 3600

  - name: "Model"
    jobs:
      - name: Model-11
        type: model
        timeout: 8200
        config:
          primary_container:
             image: "123456789012.dkr.ecr.eu-west-1.amazonaws.com/mlpipeline-repository:training_training_job"
             mode: "SINGLE_MODEL"
             model_s3_location:
                bucket: "sagemaker-eu-west-1-123456789012"
                key_prefix: "data"

          enable_network_isolation: True
          vpc: vpc-0f63e205b5c888858
          subnets:
            -
              "subnet-0ee1e02177e5fbbb8"
          tags:
              -
               project: project1
               owner: dataall

  - name: "ConfigureEndpoint"
    jobs:
      - name: EndpointConfig-11
        type: endpoint_config
        timeout: 8200
        config:
          production_variants:
            - initial_instance_count: 1
              instance_type: "m5.xlarge"
              model_name: "model-11"
              variant_name: "wind"
              initial_variant_weight: 1
          tags:
              -
               project: project1
               owner: dataall

  - name: "Serve"
    jobs:
      - name: Endpoint
        type: endpoint
        timeout: 8200
        config:
          endpoint_config_name: "EndpointConfig"

```
