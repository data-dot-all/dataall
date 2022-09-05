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
- Docker
- Yarn
- AWS credentials as environment variables:
```bash
export AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>
export AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>
export AWS_SESSION_TOKEN=<YOUR_AWS_SESSION_TOKEN>
```

## 1. Clone data.all code
data.all is fully dockerized with docker-compose, and can be started in a minute running the commands below:

```bash
git clone https://github.com/awslabs/aws-dataall.git
```

## 2. Run Docker compose

```bash
cd aws-dataall
docker-compose up
```

![dockercompose](../img/docker_compose.png#zoom#shadow)

Docker will read the credentials specified as 'default' that you have configured in your local machine, EC2 or Cloud9 or wherever you are working.

## 🎉 Congratulations 🎉
Now visit [http://localhost:8080](http://localhost:8080)

