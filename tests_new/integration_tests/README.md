# Integration tests

The purpose of these tests is to automatically validate functionalities of data.all on a real deployment.

🚨🚨🚨 Currently **we support only Cognito based deployments** 🚨🚨🚨


## Pre-requisites

- A real deployment of data.all in AWS. 
     - For this deployment the `cdk.json` flag `enable_pivot_role_auto_create` must be set to `true`.
     - For this deployment the `config.json` flag `cdk_pivot_role_multiple_environments_same_account` must be set to `true` if an AWS account is going to be reused for multiple environments, Second test account is bootstraped, and first account is added to trusted policy in target regions
        ```cdk bootstrap --trust <first-account-id> -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://<second-account-id>/region```
     - An SSM parameter (`/dataall/{env_name}/testdata`) in the DEPLOYMENT ACCOUNT with the following input parameters.
       - Test users: the 6 test users must be defined in the SSM parameter with the usernames and groups used in the 
       example. However, the password can be any password that you configure. Data.all will create this users in Cognito in the CICD pipeline. 
       - Environments: the 5 environments are mandatory fields that must be defined in the parameter. However, you need 
       to select the AWS accounts and regions to be used. The regions provided in the example can be replaced by other 
       regions. To ensure there are no cross-region issues we recommend to select the same region for both (e.g. (e.g. `session_env1` and `session_cross_acc_env_1` which in the example are both in `eu-central-1` could be deployed in `eu-west-2`)
       - Redshift and Quicksight parameters: they are optional. If not defined, the tests for Dashboards and Redshift will be skipped.
        
       
```
        {
          "users": {
            "testUserTenant": {
              "username": "testUserTenant",
              "password": "Pass1Word!",
              "groups": [
                "DAAdministrators"
              ]
            },
            "testUser1": {
              "username": "testUser1",
              "password": "Pass1Word!",
              "groups": [
                "testGroup1"
              ]
            },
            "testUser2": {
              "username": "testUser2",
              "password": "Pass1Word!",
              "groups": [
                "testGroup2"
              ]
            },
            "testUser3": {
              "username": "testUser3",
              "password": "Pass1Word!",
              "groups": [
                "testGroup3"
              ]
            },
            "testUser4": {
              "username": "testUser4",
              "password": "Pass1Word!",
              "groups": [
                "testGroup4"
              ]
            },
            "testUser5": {
              "username": "testUser5",
              "password": "Pass1Word!",
              "groups": [
                "testGroup5"
              ]
            }
          },
          "envs": {
            "session_env1": {
              "accountId": "GOLDEN_ENV_A",
              "region": "eu-central-1"
            },
            "session_env2": {
              "accountId": "GOLDEN_ENV_A",
              "region": "eu-west-1"
            },
            "persistent_env1": {
              "accountId": "GOLDEN_ENV_A",
              "region": "us-east-1"
            },
         "persistent_cross_acc_env_1": {
            "accountId": "GOLDEN_ENV_B",
            "region": "us-east-1"
          },
            "session_cross_acc_env_1": {
              "accountId": "GOLDEN_ENV_B",
              "region": "eu-central-1"
            }
          },
          "dashboards": {
            "session_env1": {
              "dashboardId": "DASHBOARD_ID"
            }
          },
           "redshift_connections": {
              "connection_serverless_admin_session_env1": {
                "namespace_id": "NAMESPACE_ID",
                "workgroup": "WORKGROUP",
                "secret_arn": "arn:aws:secretsmanager:eu-central-1:GOLDEN_ENV_A:secret:redshift!test-user-admin-serverless-X"
              },
              "connection_serverless_data_user_session_env1": {
                "namespace_id": "NAMESPACE_ID",
                "workgroup": "WORKGROUP",
                "secret_arn": "arn:aws:secretsmanager:eu-central-1:GOLDEN_ENV_A:secret:test-datauser-serverless-X"
              },
              "connection_cluster_admin_session_cross_acc_env_1": {
                "cluster_id": "test-redshift-cluster",
                "secret_arn": "arn:aws:secretsmanager:eu-central-1:GOLDEN_ENV_B:secret:redshift!test-user-admin-cluster-X"
              },
              "connection_cluster_data_user_session_cross_acc_env_1": {
                "cluster_id": "test-redshift-cluster",
                "secret_arn": "arn:aws:secretsmanager:eu-central-1:GOLDEN_ENV_B:secret:test-datauser-cluster-X"
              }
            }
        }
```


### Redshift Tests Pre-Requisities
For Redshift testing we require some pre-existing infrastructure:
  - One Redshift serverless namespace+workgroup deployed in `session_env1` and one Redshift provisioned cluster in `session_cross_acc_env_1` 
  - The provisioned cluster MUST be encrypted and use RA3 cluster type (Check the [docs](https://docs.aws.amazon.com/redshift/latest/dg/datashare-overview.html) for other data sharing limitations)
  - Both clusters must host the default `dev` database with the `public` schema.
  - For each we need to ensure that the admin credentials are stored in Secrets Manager. The secrets MUST be tagged with the tag {key:dataall, value:True}. If you are going to use the Redshift Query Editor, then you will also need the tag {key:Redshift, value:any}
  - For each we need to create a Redshift user (see SQL commands below) and store the credentials in Secrets Manager. The secrets MUST be tagged with the tag {key:dataall, value:True}. If you are going to use the Redshift Query Editor, then you will also need the tag {key:Redshift, value:any}
  - For each we need to create a set of tables using the commands below
  - For each we need to create a Redshift role as in the commands below

Create User and grant basic permissions using admin connection
```sql
CREATE USER testuser PASSWORD 'Pass1Word!';
GRANT USAGE ON SCHEMA public TO testuser;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO testuser;
```

Create and attach role using admin connection
```sql
CREATE ROLE testrole;
GRANT ROLE testrole TO testuser;
```

Create tables using testuser connection
```sql
DROP TABLE IF EXISTS nation;
DROP TABLE IF EXISTS region;

CREATE TABLE region (
  R_REGIONKEY bigint NOT NULL,
  R_NAME varchar(25),
  R_COMMENT varchar(152))
diststyle all;

CREATE TABLE nation (
  N_NATIONKEY bigint NOT NULL,
  N_NAME varchar(25),
  N_REGIONKEY bigint,
  N_COMMENT varchar(152))
diststyle all;
```

### Dashboard Tests Pre-Requisities

In order to run the tests on the dashboards module the following steps are required:

- Create Enterprise QuickSight Subscription in `session_env1` AWS Account
- Update QuickSight Account with a Reader Capacity Pricing Plan (required for generating embed URLs - `GenerateEmbedUrlForAnonymousUser`)
- Create / Publish a QuickSight Dashboard
- Create a QuickSight Group named `dataall` and give owner access of the published dashboard to the `dataall` group
- Provide the `dashboardId` in the `config.json` as shown above

Rather than failing if the above pre-requisites are not completed, if ther eis no QuickSight Account is detected in `session_env1` the dashboard tests will be **skipped**.

## Run tests

The tests are executed in CodeBuild as part of the CICD pipeline if the cdk.json parameter `with_approval_tests` is set
to True.

You can also run the tests locally by...

* Authenticating to your data.all environment account (you might want to set the `AWS_PROFILE` env variable)

* ```bash
  export ENVNAME = "Introduce deployment environment name"
  export AWS_REGION = "Introduce backend region"
  export COGNITO_CLIENT = "Introduce Cognito client id"
  export API_ENDPOINT = "Introduce API endpoint url"
  echo "add your testdata here" > testdata.json 
  make integration-tests
  ```
## Remarks
### Global and local conftest

There is a top-level `conftest` file that defines the global fixtures of the tests such as users, clients...

In each of the modules, we will use `conftest` files to define fixtures used in the module. If a fixture is used in other modules it should be
defined in a `globconftest` file and then imported in the global `conftest` in the `pytest_plugins`.


### External AWS API calls
There are some tests that need to perform AWS actions outside of data.all. For example, in the case of data.all imported datasets
the API requires an existing S3 Bucket. Another example is the validation of successful share requests, which to be fully validated
the data is actually accessed by the requester IAM role outside of data.all API calls. 

To automate these usually manual processes, an IAM `integration-tests-role` is created as part of the data.all Environment stack when the
`EnvironmentType=IntegrationTesting`. The EnvironmentType is defined programmatically when we create an Environment using the API.

The `integration-tests-role` has a trust policy and can be assumed by the CICD account. The specific boto3 calls that call
AWS are centralized in the `aws_clients/` directory.

### Persistence of resources
- Persistent resources must always be present (if not i.e first run they will be created but won't be removed). They are suitable for testing backwards compatibility. 
- Session resources persist across the duration of the whole integration test suite and are meant to make the test suite run faster (env creation takes ~2 mins). For this reason they must stay immutable as changes to them will affect the rest of the tests.
- Temporary resources will be created and deleted per test, use with caution as they might increase the runtime of the test suite. They are suitable to test the resource mutations.

