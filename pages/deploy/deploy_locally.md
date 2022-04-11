---
layout: default_sublevel
title: Deploy to AWS
permalink: /deploy-locally/
---

# **Getting Started: Deploy locally**

**We** ❤️‍🔥 **Dev teams**. data.all provides a local developer experience, allowing the data.all backend
to run locally. Local development experience allows teams to implement,
test and release new features quickly and easily.

## Option 1: Docker compose
### Prerequisites

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

### 1. Clone data.all code
data.all is fully dockerized with docker-compose, and can be started in a minute running the commands below:

```bash
git clone https://github.com/awslabs/aws-dataall.git
cd aws-dataall
```

### 2. Run Docker compose

```bash
cd data.all
docker-compose up
```

![dockercompose](../img/docker_compose.png#zoom#shadow)

### 🎉 Congratulations 🎉
Now visit [http://localhost:8080](http://localhost:8080)

## Option 2: servers + docker

data.all can also be started locally, with a mix of pure python servers and docker. It's obviously harder but it's easier to debug your code this way.
### Prerequisites

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


### 1. Launch Docker containers
Launch a postgres database, an Elasticsearch cluster and Kibana on your local computer with Docker:

```bash
docker run -d  --name pg -p 5432:5432 -e POSTGRES_PASSWORD=docker -e POSTGRES_USER=postgres -e POSTGRES_DB=data.all -t postgres:10
docker run -d --name elasticsearch   -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" elasticsearch:7.9.3
docker run --link elasticsearch:elasticsearch -p 5601:5601 docker.elastic.co/kibana/kibana:7.9.3
```
The PostgreSQL instance has the following characteristics:
- user : `postgres`
- password: `docker`
- database:  `data.all`

Note: Kibana UI can be accessed at http://localhost:5601/app/home

### 2. Create Postgres schemas

You now have to create two schemas (`local` and `pytest`) in the `data.all` database running on your computer. To do so, open a new terminal window and run:
```bash
docker exec -it pg bash
```
Once connected to the container run:
```bash
psql -U postgres
```
Then connect to the data.all database:
```bash
\connect data.all # there should be only one backslash !
```
Finally create the schemas in exit the container
```sql
create schema local;
create schema pytest;
```
You may now close the terminal window.

### 3. Create secret in Secrets Manager

The next step is to create a new secret in Secrets Manager. data.all gets the value of this secret to access the local database instance. Connect to the AWS console and create a new secret named **data.all-externalId-local**. Store the value **docker** in a plaintext format. **docker** is the password set for the local postgres instance deployed earlier.



### 4. Add data.all backend repository into the python path

Open backend/data.all/cdkproxy/stacks/cdk_cli_wrapper.py file and locate the following line of code:
```python
python_path = '/:'.join(sys.path)[1:] + ':/code'
```

To import all data.all modules, you need to add the backend absolute path to the python path. So if your absolute path is */local/home/name/Desktop/data.all/backend*, edit the line in the cdk_cli_wrapper.py as follows:
```python
python_path = '/:'.join(sys.path)[1:] + ':/code' + ':/local/home/name/Desktop/data.all/backend'
```

### 5. Run Python scripts

First, open file data.all-backend-dev/src/local.graphql.server.py and uncomment the following line of code:
```python
- #create_schema_and_tables(engine, envname=ENVNAME)
+ create_schema_and_tables(engine, envname=ENVNAME)
```
⚠️ This line of code deletes everything in the local postgres database, and creates all the data.all tables in the local schema. So make sure that you uncomment this line only during the first execution of the python script. Otherwise, it will delete all the data.all metadata you already have locally.

Then run the following commands:
```bash
cd data.all
python3.7 -m virtualenv .venvdh
source .venvdh/bin/activate
```
At this point you should be inside your virtual environment.


**PyGreSQL** library is used to manage the connection pool to PostgreSQL database.
It requires **postgresql** tool to be installed on your machine.

Depending on your OS, choose the relevant command to install **postgresql**:

AmazonLinux-CentOS
```bash
yum -y install openssl-devel bzip2-devel libffi-devel postgresql-devel python38-devel gcc unzip tar gzip
```

Ubuntu
```bash
apt-get install -yq libpq-dev postgresql postgresql-contrib
```

MacOS
```bash
brew install postgresql
```

### 6. Install Python requirements
```
pip install -r requirements.txt
pip install -r backend/requirements.txt
pip install -r backend/data.all/cdkproxy/requirements.txt
python backend/local.graphql.server.py
python backend/local.cdkapi.server.py
```
You should see the following if you have successfully running local.graphql.server.py:
![Screenshot](../assets/successfully_running_graphql_server.png#zoom#shadow)



You should see the following if you have successfully running local.cdkapi.server.py:
![Screenshot](../assets/successfully_running_cdkapi_server.png#zoom#shadow)


You can check that this has been successful by clicking on this link: **[http://localhost:2805](http://localhost:2805)**
You should see a 'Service is up' message.


data.all's backend is now deployed on your computer!

### 7. Deploy the frontend

To deploy data.all's frontend without docker:
```bash
cd data.all/frontend
npm install
npm run start
```
### 🎉 Congratulations 🎉
data.all's backend and frontend is now deployed on your computer.
Now visit [http://localhost:8080](http://localhost:8080)
