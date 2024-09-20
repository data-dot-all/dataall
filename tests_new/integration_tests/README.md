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
                       "accountId": "another acc",
                       "region": "same as session_env1"  
               },
            }
          }
          ```
- The pipeline will create the users/groups

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

## Coverage

At the moment integration tests cover:
- Organizations
- Environments
- S3 Datasets
- Notebooks
- Worksheets