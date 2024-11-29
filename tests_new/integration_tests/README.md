# Integration tests

The purpose of these tests is to automatically validate functionalities of data.all on a real deployment.

🚨🚨🚨

Currently **we support only Cognito based deployments** but support for any IdP is on the plans

🚨🚨🚨

## Pre-requisites

- A real deployment of data.all in AWS. 
     - For this deployment the `cdk.json` flag `enable_pivot_role_auto_create` must be set to `true`.
       - For this deployment the `config.json` flag `cdk_pivot_role_multiple_environments_same_account` must be set to `true` if an AWS account is going to be reused for multiple environments,
         - Second test account is bootstraped, and first account is added to trusted policy in target regions
          ```cdk bootstrap --trust <first-account-id> -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://<second-account-id>/region```
         - An SSM parameter (`/dataall/{env_name}/testdata`) in the DEPLOYMENT ACCOUNT with the following contents
          ```
          {
            "users": {
              "testUserTenant": {
                "username": "testUserTenant",
                "password": "...",
                "groups": [
                  "DAAdministrators"
                ]
              },
              "testUser1": {
                "username": "testUser1",
                "password": "...",
                "groups": [
                  "testGroup1"
                ]
              },
              "testUser2": {
                "username": "testUser2",
                "password": "...",
                "groups": [
                  "testGroup2"
                ]
              },
              "testUser3": {
                "username": "testUser3",
                "password": "...",
                "groups": [
                  "testGroup3"
                ]
              },
              "testUser4": {
                "username": "testUser4",
                "password": "...",
                "groups": [
                  "testGroup4"
                ]
              }
            },
              "envs": {
              "session_env1": {
                "accountId": "...",
                "region": "eu-central-1"
              },
              "session_env2": {
                "accountId": "...",
                "region": "eu-west-1"
              },
              "persistent_env1": {
                "accountId": "...",
                "region": "us-east-1"
              },
               "persistent_cross_acc_env_1": {
                  "accountId": "...",
                  "region": "us-east-1"
                },
              "session_cross_acc_env_1": {
                "accountId": "...",
                "region": "eu-central-1"
              }
            },
            "dashboards": {
                "session_env1": {
                  "dashboardId": "..."
                },
              },
             "redshift_connections": {
              "connection_serverless_admin_session_env1": {
                "namespace_id": "...",
                "workgroup": "...",
                "secret_arn": "..."
              },
              "connection_serverless_data_user_session_env1": {
                "namespace_id": "...",
                "workgroup": "...",
                "secret_arn": "..."
              },
              "connection_cluster_admin_session_cross_acc_env_1": {
                "cluster_id": "...",
                "secret_arn": "..."
              },
              "connection_cluster_data_user_session_cross_acc_env_1": {
                "cluster_id": "...",
                "secret_arn": "..."
              }
            }
          }
          ```

- The pipeline will create the users/groups
- For Redshift testing we require some pre-existing infrastructure:
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
  export IDP_DOMAIN_URL = "Introduce your Identity Provider domain url"
  export DATAALL_DOMAIN_URL = "Introduce data.all frontend domain url"

  echo "add your testdata here" > testdata.json 
  make integration-tests
  ```

## Coverage

At the moment integration tests cover:
- Organizations
- Environments
- S3 Datasets
- Notebooks
- Worksheets