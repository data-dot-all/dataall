# Athena task
The codes for AWS Athena in data.all data pipeline in the step function.

## How to declare an Athena task in the general config.yaml
To include an Athena task in a step function, it is mandatory to define the path to the athena.yaml config file.
In the following example, "customcode/athena/athena_jobs/example.yaml". Other parameters such as workgroup, retry strategy and variables are optional
Remember that steps inside groups are executed in sequence, while the jobs inside a step are executed in parallel.
```yaml
groups:
  - name: Step2WithAthena
    jobs:
      - name: MyAthenaFunction
        type: athena_query
        comment: "[Optional] describe me please"
        config:
          config_file: "customcode/athena/athena_jobs/example.yaml" # it configures the athena job
          workgroup: MyAthenaWGName # [Optional], we can reference the previously created workgroup
          # If no workgroup is assigned, then the environment-AD group workgroup is chosen by default
          retry: # [Optional], if no retry parameters are assigned, no retry strategy is configured
            error_equals: ["Athena.AmazonAthenaException","Athena.TooManyRequestsException"]
            interval_seconds: 1
            retry_attempts: 5
            backoff_rate: 2
          variables: # [Optional] we can pass variables and referenced variables
            dimension : classification
            model_name : {{model_name_in_var_file}}
```
## How to define the config files for athena
The yaml file consists of steps that contain jobs. As in the general config.yaml steps are executed in sequence and jobs inside the same step in parallel, thus allowing more complicated step function structures.
For each job we have to define the type, which can be either an sql query reference or a prepared statement created in the aws_resources section.
```yaml
# example.yaml in customcode/athena/athena_jobs/

steps:
  - name: Example_Step_01
    jobs:
    # Introduce here the different steps, queries to run in parallel
    - name : example_name_pre
      type: sql
      config:
        file: "customcode/athena/sql_queries/{{model_name}}/example.sql"

    - name : example_name_int
      type: sql
      config:
        file: "customcode/athena/sql_queries/{{dimension}}/example.sql"

  - name: Example_Step_02
    jobs:
    # Introduce here the different steps, queries to run in parallel
    - name : example_prepared_statement
      type: prepared_statement
      config:
        prepared_statement: MyPreparedStatement
```

# How to pass variables
- the general variables.yaml file: declared used to replace values in the general config.yaml does NOT replace values in the athena yaml config files. Therefore, {{model_name_in_var_file}} can only be referenced in the general config.yaml.

- variables in the config.yaml under config/variables: are passed and replaced in the athena config files. For example, {{dimension}} and {{model_name}}.* These variables are also replaced in the SQL query code defined in the SQL file. For example:

```sql
-- In "customcode/athena/sql_queries/{{dimension}}/example.sql"
DROP TABLE IF EXISTS {{model_name}}.stg_dim_{{dimension}};
  ```
