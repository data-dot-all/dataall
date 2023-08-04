---
layout: default
homePage: false
title: Basic Concepts
permalink: /concepts/
---
# **Basic Concepts**

This section is an overview of the main components of data.all which are divided in 3 groups:

- **Administrate**: used by team and data lake administrators to organise and manage teams and users inside data.all
- **Discover**: used by all users to contribute with data, search for data and share data.
- **Play**: once data is in data.all, all users can use these tools to work with data.


## Administrate

### Organizations
Organizations are high level constructs where business units can collaborate across different AWS accounts
at once. An organization includes environments (see below). Organizations are abstractions, they **don't** contain AWS
resources, consequently there is no CloudFormation stack associated with them.

*Organizations usually correspond to whole organizations, organization divisions, departments or geographical regions
within an organization.*

### Environments
An Environment is an AWS workspace where a teams store and work with data and build data driven applications.
This workspace is mapped to an AWS account in one region. It is possible to have more than one environment in the same
AWS Account, however we recommend to stick to one environment -  one account.

*An environment usually corresponds to a business unit or a department. Inside an environment we add teams and
assign them different levels of permissions.*

### Teams
A Team corresponds to an IdP group that has been onboarded to data.all.  As with IdP groups, users can
belong to multiple teams. Data in data.all is isolated at team level, meaning that all members of a team can access all team's datasets.
Thus, a team is any group of users that can access the team's datasets. We can have bigger teams with generic data
and project-based teams owning data that requires more restrictive access to only members of the project.

A special case for the administration of
data.all is the **Tenant** team, an IdP group with high level application (tenant) permissions.

*Teams corresponds to real teams.*


## Discover
### Datasets
A Dataset is a representation of multiple AWS resources that helps users store data.
When data owners create a dataset on data.all the following resources are created:

- Amazon S3 Bucket to store the data on AWS.
- AWS KMS key to encrypt the data on AWS.
- AWS IAM role that gives access to the data on Amazon S3.
- AWS Glue database that is the representation of the structured data on AWS.

*Inside the dataset we can store structured data as tables or unstructured data in folders.*

### Catalog
data.all centralized Catalog is an inventory of datasets, tables, folders and dashboards. It contains metadata for each
of the mentioned data assets and thanks to its search capabilities, users can filter based on type of data, type of
asset, tags, region and on glossary terms.

*We use the Catalog to search and discover data*

### Glossaries
A Glossary is a hierarchical tree of terms, created and maintained by a team to label data with their specific taxonomies.
For example, terms like "cost", "revenue", etc, can be used to group and search all financial datasets.

*Glossaries are used to add meaning and business context to data assets facilitating and enhancing Catalog searching*

### Shares
A Share is an access request to a data asset. Users search and discover data in the catalog and for those data assets
that belong to other teams, users can create a Share on behalf of a team (remember, data access: at team level!!). Then,
the owners of the asset can accept or reject the share.

*We use Shares to collaborate and share data with other teams.*

## Play
### Worksheets
Worksheets are AWS Athena sessions that allow us to query our datasets as if we were in the AWS Athena Query editor
console.

### Notebooks
Data practitioners can experiment machine learning algorithms
spinning up Jupyter notebook with access to all your datasets. data.all leverages
<a href="https://docs.aws.amazon.com/sagemaker/latest/dg/nbi.html" target="_blank">
Amazon SageMaker instance</a> to access Jupyter notebooks.

### ML Studio
With ML Studio Notebooks we can add users to our SageMaker domain and open Amazon SageMaker Studio.

### Pipelines
In order to distribute data processing, data.all introduces data.all pipelines where:
- data.all takes care of CI/CD infrastructure
- data.all offers flexible pipeline blueprints to deploy AWS resources

### Dashboards
In the Dashboard window we can start Quicksight sessions, create visual analysis and dashboards.
