# **What's data.all**

A modern data workspace that makes collaboration among diverse users (like business, analysts and engineers) easier, increasing efficiency and agility in data projects ✨

![data.all_catalog](documentation/userguide/docs/pictures/catalog/catalog_readme.png)
## **Why we built data.all**

Using **data.all**, any line of business within an organization can create their own isolated data lake, produce, consume and share data within and across business units, worldwide.

By simplifying data discovery, data access management while letting more builders use AWS vast portfolio of data and analytics services.

**data.all** helps more data teams discover relevant data and let them use the power of the AWS cloud to create data driven applications faster.


## Quick start

### Prerequisites

1. **docker** up and running on your machine.
2. **nodejs** and **yarn** installed on your machine.
3. AWS account credentials exported as environment variables. data.all will use it to create AWS resources.

### Run commands
```bash
git clone https://github.com/awslabs/aws-dataall.git
cd dataall
docker-compose up
```

Now visit [http://localhost:8080](http://localhost:8080)

## Documentation

### User Guide
```bash
cd dataall/documentation/userguide
pip install -r requirements.txt
mkdocs serve
```

### Dev Guide
```bash
cd dataall/documentation/devguide
pip install -r requirements.txt
mkdocs serve
```

## Security issue notifications
If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.
