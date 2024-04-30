# Integration tests
The purpose of these tests is to automatically validate functionalities of data.all on a real deployment.

## Pre-requisites
- A real deployment of data.all in AWS
- 4 Cognito users (at the moment only Cognito is supported) like the ones defined in `conftest`(e.g. `testUser1` with password `Pass1Word!`)

## Run tests

The tests are executed in CodeBuild as part of the CICD pipeline if the cdk.json parameter `with_approval_tests` is set to True.

But you can also run the tests locally with deployment account credentials:
```bash
export ENVNAME = "Introduce deployment environment name"
export AWS_REGION = "Introduce backend region"
make integration-tests
```

or run the tests locally without credentials:
```bash
export ENVNAME = "Introduce deployment environment name"
export AWS_REGION = "Introduce backend region"
export COGNITO_CLIENT = "Introduce Cognito client id"
export API_ENDPOINT = "Introduce API endpoint url"
make integration-tests
```

## Coverage
At the moment integration tests only cover Organizations module as an example.