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

## 1. Clone data.all code
data.all is fully dockerized with docker-compose, and can be started in a minute running the commands below:

```bash
git clone https://github.com/awslabs/aws-dataall.git
```

## 2. Run Docker compose

With docker compose we orchestrate the build of 5 containers: frontend, db, graphql, cdkproxy, opensearch.
You can check the ports assigned to each container in the `docker-compose.yaml` file at the root level of the repo.

```bash
cd aws-dataall
docker-compose up
```

![dockercompose](../img/docker_compose.png#zoom#shadow)

🎉 **Congratulations** 🎉 Now you can access the UI in [http://localhost:8080](http://localhost:8080)

## 3. Set AWS credentials
Docker will read the AWS credentials specified as 'default' that you have configured in your local machine, EC2 or Cloud9 or wherever you are working.

This is how your `.aws/credentials` file should look like:
```
[default]
aws_access_key_id=XXXXXXX
aws_secret_access_key=XXXXX
aws_session_token=XXXXXXX
```
In theory, you can choose any AWS account. However, there are some functionalities, e.g. linking an environment,
where the AWS accounts used need some preparation. As a rule of thumb, if your local development needs to interact with other
AWS accounts, you should check out the next section.

## 4. Linking environments

As it is explained in the architecture section, data.all communicates with the environment accounts through 2 mechanisms:
1) CDK bootstrap `--trust` to the data.all central account: the AWS account chosen to link the environment needs to be bootstraped trusting the AWS account that 
you used in step 3.


2) IAM Pivot Role trusting the data.all central account with an external ID. Whenever we perform an AWS SDK call to the environment account you will be assuming the Pivot Role in that account.
To be able to assume it, you need to provide an external ID with the call. In a real deployment, the external ID
is read from AWS Secrets Manager, for a local deployment we have 2 options to recreate this setup. After that you can go 


### Create a `dkrcompose` externalId secret in the credentials account

This option is especially suitable for those using an AWS account that already has data.all deployed. The only
necessary step is to create a secret in AWS Secrets Manager called `dataall-externalId-dkrcompose` with the 
value of the secret `dataall-externalId-<envname>`.

![dockercompose](../img/docker_compose_secrets.png#zoom#shadow)

After that, you can go ahead and download the CloudFormation YAML template from the UI and introduce the parameters
that you can copy from the UI.













