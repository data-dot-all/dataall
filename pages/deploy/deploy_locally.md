---
layout: default_sublevel
title: Deploy to AWS
permalink: /deploy-locally/
---

# **Getting Started: Deploy locally**

**We** ❤️‍🔥 **Dev teams**. data.all provides a local developer experience, allowing the data.all backend
to run locally. Local development experience allows teams to implement,
test and release new features quickly and easily.

## Prerequisites

Depending on your OS, you will need the following:

- Python >= 3.7
- Docker, Docker-compose >= 2
- node
- Yarn
- AWS credentials as environment variables.

## 1. Clone data.all code and run docker compose
data.all is fully dockerized with docker-compose, and can be fully run from your local computer. 
The first step is to clone the repo.

```bash
git clone https://github.com/data-dot-all/dataall.git --branch v2.3.0
```

With docker compose we orchestrate the build of 5 containers: frontend, db, graphql, cdkproxy, opensearch.
You can check the ports assigned to each container in the `docker-compose.yaml` file at the root level of the repo.

```bash
cd dataall
export UID && docker-compose up
```

**Note:** We export `UID` to ensure the docker user created to run the container has the correct permissions to read from the mounted file systems for the locally deployed data.all.

![dockercompose](../img/docker_compose.png#zoom#shadow)

🎉 **Congratulations** 🎉 Now you can access the UI in [http://localhost:8080](http://localhost:8080)

## 2. Set AWS credentials
You can access the UI, but until you set AWS credentials you won't be able to create Environments, Datasets or any
other data.all stack.

We have configured Docker to read the AWS credentials specified in the 'default' profile that you have configured in your local machine, EC2 or Cloud9 or wherever you are working.

You can use credentials for any AWS account, but we recommend you to use an AWS account that you currently use as infrastructure account of data.all.
This is how your `.aws/credentials` file should look like:
```
[default]
aws_access_key_id=XXXXXXX
aws_secret_access_key=XXXXX
aws_session_token=XXXXXXX
```

## 3. Create parameters in credentials AWS account
Data.all reads some parameters from SSM, thus we need to create them in the selected AWS account to fully work with data.all.

Create a `dkrcompose` externalId for the pivot role parameter in the credentials account with the following command.
```bash
aws ssm put-parameter \
    --name "/dataall/dkrcompose/pivotRole/externalId" \
    --value "randomvalue1234" \
    --type String \
```
And the `dkrcompose` pivot role name parameter.
```bash
aws ssm put-parameter \
    --name "/dataall/dkrcompose/pivotRole/pivotRoleName" \
    --value "dataallPivotRole" \
    --type String \
```
Finally, set the value for the enable pivot role auto-creation
```bash
aws ssm put-parameter \
    --name "/dataall/dkrcompose/pivotRole/enablePivotRoleAutoCreate" \
    --value "False" \
    --type String \
```


## 4. Linking environments

As it is explained in the architecture section, data.all communicates with the environment accounts through 2 mechanisms:
1) CDK bootstrap `--trust` to the data.all central account: the AWS account chosen to link the environment needs to be bootstraped trusting the AWS account that 
you used in step 2 and 3.

2) IAM Pivot Role trusting the data.all account used in 2 and 3. When we create the pivot role stack in the environment account, use
the account specified in 2 and 3 and the externalId and pivotRole name defined in 3.














