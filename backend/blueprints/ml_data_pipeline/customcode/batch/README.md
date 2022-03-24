# Batch task
The codes for AWS Batch in data.all data pipeline in the step function.
The definition of compute environment, job queue, are defined under resource_task.py.

## How to declare a batch task.
To include a batch task in a step function, the most important is to declare the job definition and job queue.
You can declare job definition in an embedded way such as:


```yaml
 		 name : cat_image
         type: batch
         job_queue_param: {{batch_job_queue_param}}

         job_definition:
         	name: cat_image_processing
         	container_properties:
	           image:
	             assets:
	              directory: customcode/batchpy
	              file: Dockerfile

         command:
               - -b
               - dhcatsig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"

```
See a complete way on how to define a job_definition under resource_task documentation.

Or, you can also refer the batch job definition that is created in the same config.yaml:

```yaml
aws_resources:

  - name: cat_image_processing
    type: batch_job_definition
    job_definition:
         container_properties:
           image:
             assets:
              directory: customcode/batchpy
              file: Dockerfile

groups:
  - name: cat_image_manipulation
    jobs:
       - name : cat_image
         type: batch
         job_queue_param: {{batch_job_queue}}
         job_definition_ref: cat_image_processing
         config:
           command:
               - -b
               - dhcatsig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"
```

You can also refer to the batch job definition ARN directly

```yaml

		 name : cat_image
         type: batch
         job_queue_param: {{batch_job_queue}}
         job_definition_arn: arn:aws:batch:eu-west-1:123456789012:job-definition/catimage:1
         config:
           command:
               - -b
               - dhcatsig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"
```

Finally, you can refer batch job definition from Parameter Store
```yaml
		 name : cat_image
         type: batch
         job_queue_param: {{batch_job_queue}}
         job_definition_arn_from_path: $.batch_job_definition
         config:
           command:
               - -b
               - dhcatsig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"
```

## How to declare a job queue

You can declare job_queue also in the same ways as job definition:
1. Job queue ARN directly or from path
2. Job queue ARN from Parameter store
3. Job queue reference when job queue is defined in the same config.yaml.

```yaml
 -  name: cat_image_manipulation
    # example of job queue declared directly using ARN
    jobs:
       - name : cat_image
         type: batch

         job_queue_arn: arn:aws:batch:eu-west-1:123456789012:job-queue/queuebatchjobqueue
         job_definition:
         	name: cat_image_processing
         	container_properties:
	           image:
	             assets:
	              directory: customcode/batchpy
	              file: Dockerfile

         command:
               - -b
               - dhcatsig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"

```

Similarly, from path:

```yaml
 -  name: cat_image_manipulation
    # example of job queue declared directly using ARN
    jobs:
       - name : cat_image
         type: batch

         job_queue_arn_from_path: $.job_queue
         job_definition:
          name: cat_image_processing
          container_properties:
             image:
               assets:
                directory: customcode/batchpy
                file: Dockerfile

         command:
               - -b
               - dhcatsig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"

```

Or, from Parameter Store:

```yaml
         name : cat_image
         type: batch
         job_queue_param: {{pipeline_name}}/job_definition/default_job_queue
         job_definition_ref: cat_image_processing
         config:
           command:
               - -b
               - dhairlinesig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"
```

Using reference:

```yaml
aws_resources:

  - name: my_compute_environment
    type: batch_compute_environment

    properties:
       compute_resource_type: SPOT
       bid_percentage: 100
       subnet_from_cloudformation: "vpc-public-cf-SubnetTier2List"
       vpc_from_cloudformation: "vpc-public-cf-VpcId"

  - name: my_batch_job_queue
    type: batch_job_queue
    properties:
      compute_environment:
         compute_environment_ref:
            - my_compute_environment

  - name: cat_image_processing
    type: batch_job_definition
    job_definition:
         container_properties:
           image:
             assets:
              directory: customcode/batchpy
              file: Dockerfile

groups:
  - name: cat_image_manipulation
    jobs:
       - name : cat_image
         type: batch
         job_queue_ref: my_batch_job_queue
         job_definition_ref: cat_image_processing
         config:
            command:
               - -b
               - dhairlinesig5t7deuwest1
               - -o
               - cats
               - -d
               - transformed_cats
               - --height
               - "120"
               - --width
               - "210"
```

## Container Overrides
Set of properties to override default values from job definition. All the supported properties have the corresponding from_path parameter that allows to define the properties from input path.

The following properties are supported:
1. command or command_from_path. To override the command defined in the job definition.
2. environment or environment_from_path. To override the environment variables of job definition.
3. gpu_count or gpu_count_from_path. The number of GPUs
4. instance_type or instance_type_from_path. The instance type
5. memory_size the memory size
6. vcpus, the number of vcpus.
Note that command and environment can also be defined outside container_overrides block.

```yaml
name : cat_image
         type: batch
         job_queue_param: {{nnq_batch_job_queue}}
         job_definition_ref: cat_image_processing
         config:
            container_overrides:
              vcpus: 4
              command:
                 - -b
                 - dhairlinesig5t7deuwest1
                 - -o
                 - cats
                 - -d
                 - transformed_cats
                 - --height
                 - "120"
                 - --width
                 - "210"
```

# Other properties
In addition to job definition, job queue, and container overrides, the following are the properties supported by batch_task in data.all:
1. depends_on
2. propagate_tags.
3. attempts.


- Override containers
