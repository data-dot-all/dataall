# **Datasets**
## **Datasets**
In data.all, a Dataset is a representation of multiple AWS resources that helps
users store data and establish the basis to make this data discoverable and shareable with other teams.

When data owners create a dataset the following resources are
deployed on the selected environment and its linked AWS account:

1.  Amazon S3 Bucket to store the data on AWS.
2.  AWS KMS key to encrypt the data on AWS.
3.  AWS IAM role that gives access to the data on Amazon S3.
4.  AWS Glue database that is the representation of the structured data on AWS.

!!!abstract "AWS Champion"
    data.all does all the infrastructure heavy lifting for data owners using
    **AWS CDK** and **AWS CloudFormation** service while following AWS
    deployment and security best practices.

### Tables and Folders

Inside a dataset we can store structured data in tables and unstructured data in folders.

- Tables are the representation of **AWS Glue Catalog** tables that are created on the dataset's Glue database on AWS.
- Folders are the representation of an **Amazon S3 prefix** where
data owners can organize their data. For example, when data is loaded, it
can go to a folder named “raw” then after it's processed the data moves
to a folder called “silver” and so on.


### Dataset ownership
Dataset ownership refers to the ability to access, modify or remove data from a dataset, but also to the responsibility
of assigning these privileges to others.

- **Owners**: When you create a dataset and associate it with a team, the dataset
business ownership belongs to the associated team.

- **Stewards**: You can delegate the stewardship of a dataset to a team of stewards. You can type a name of an IdP group or choose
one of the teams of your environment to be the dataset stewards.

!!!note
    Dataset owners team is a required, non-editable field, while stewards are optional and can be added post the
    dataset has been created. If no other stewards team is designated, the dataset owner team will be the only
    responsible in managing access to the dataset.

### Dataset access
In this case we are referring to the ability to access, modify or remove data from a dataset. Who can access the
dataset content? users belonging to...

- the dataset owner team
- a dataset steward team
- teams with a share request approved to dataset content

!!!note
    Dataset metadata is available for all users in the centralized data catalog.


## :material-new-box: **Create a dataset**

On left pane choose **Datasets**, then click on the **Create** button. Fill the dataset form.

![create_dataset](pictures/datasets/dat_create_form.png#zoom#shadow)

| Field             | Description                                               | Required        | Editable |Example
|-------------------|-----------------------------------------------------------|-----------------|----------|-------------
| Dataset name  | Name of the dataset                                       | Yes             | Yes      |AnyDataset
| Short description | Short description about the dataset                       | No              | Yes      |For AnyProject predictive model
| Environment   | Environment (mapped to an AWS account)                    | Yes             | No       |DataScience
| Region (auto-filled)            | AWS region of the environment                             | Yes             | No       |Europe (Ireland)
| Organization (auto-filled)     | Organization of the environment                           | Yes             | No       | AnyCompany EMEA
| Owners    | Team that owns the dataset                                | Yes             |   No       | DataScienceTeam
| Stewards    | Team that can manage share requests on behalf of owners   | No              |  Yes        |  FinanceBITeam, FinanceMgmtTeam
| Confidentiality  | Level of confidentiality: Unclassified, Oficial or Secret | Yes             | Yes      | Secret
| Topics           | Topics that can later be used in the Catalog              | Yes, at least 1 | Yes       | Finance
| Tags             | Tags that can later be used in the Catalog                | Yes, at least 1 | Yes      | deleteme, ds


## :material-import: **Import a dataset**

If you already have data stored on Amazon S3 buckets in your data.all environment, data.all got you covered with the import feature. In addition to
the fields of a newly created dataset you have to specify the S3 bucket and optionally a Glue database:

| Field             | Description                                                                | Required | Editable |Example
|-------------------|----------------------------------------------------------------------------|----------|----------|-------------
| Amazon S3 bucket name  | Name of the S3 bucket you want to import           | Yes      | No    |importedBucket
| AWS Glue database name | Name of the Glue database tht you want to import         | No       | No      |anyDatabase

![import_dataset](pictures/datasets/import_dataset.png#zoom#shadow)

## :material-card-search-outline: **Navigate dataset tabs**

**When we belong to the dataset owner team**

After creating or importing a dataset it will appear in the datasets list (click on Datasets on the left side pane).
In this window, it will only ve visible for those users belonging to the dataset owner team. If we select one of our
datasets we will see the following dataset window:

![with](pictures/datasets/data_with_access.png#zoom#shadow)

**When we DON'T belong to the dataset owner team**

How do we access a dataset if we don't have access to it? IN THE CATALOG! on the left pane click on Catalog, find the
dataset you are interested in, click on it and if you don't have access to it, you should see only some of the tabs
in comparison with the previous pic, something like:

![without](pictures/datasets/data_without_access.png#zoom#shadow)

## :material-pencil-outline: **Edit and update a dataset**
Data owners can edit the dataset by clicking on the **edit** button, editing the editable fields and saving the changes.

## :material-trash-can-outline: **Delete a dataset**
To delete a dataset, in the selected dataset window click on the **delete** button in the top-right corner. As with
environments, it is possible to keep the AWS CloudFormation stack to keep working with the data and resources created
but outside of data.all.

## :material-aws: **Check dataset info and access AWS**
The **Overview** tab of the dataset window contains dataset metadata, including governance and creation details.
Moreover, AWS information related to the resources created by the dataset CloudFormation stack can be consulted here:
AWS Account, Dataset S3 bucket, Glue database, IAM role and KMS Alias.

You can also assume this IAM role to access the S3 bucket in the AWS console by clicking on the **S3 bucket** button.
Alternatively, click on **AWS Credentials** to obtain programmatic access to the S3 bucket.

![overview](pictures/datasets/dataset_overview.png#zoom#shadow)

## :material-basket-fill: **Fill the dataset with data**

### Tables

**Quickly upload a file for data exploration**

Users may want to experiment with a small set of data (e.g. a csv file). To create tables from a file,
we first upload the file, then run the crawler to infer its schema, and finally, we read the
schema by synchronizing the table. Upload & Crawl & Sync

1. Upload data: Go to the **Upload** tab of the dataset and browse or drop your sample file. It will be uploaded to the
dataset S3 bucket in the prefix specified. By default, a Glue crawler will be triggered by the
upload of a file, however this feature can be disabled as appears in the picture.

![upload](pictures/datasets/dataset_table_upload.png#zoom#shadow)

2. Crawl data: the file has been uploaded but the table and its schema have not been registered in the dataset
Glue Catalog database. If you have disabled the crawler in the upload, click on the **Start Crawler** button in the
Data tab. If you just want to crawl one prefix, you can specify it in the Start Crawler feature.


![crawl](pictures/datasets/dataset_crawl.png#zoom#shadow)

3. Synchronize tables: Once crawled and registered in the Glue database, you can synchronize tables from your
dataset's AWS Glue database by using **Synchronize** tables feature in the Data tab. In any case,
data.all will synchronize automatically the tables for you at a frequency of **15 minutes**.

You can preview your small set of data right away from data.all, check <a href="tables.html">Tables</a>.


**Ingest data**

If you need to ingest larger quantities of data, manage bigger files, or simply you cannot work with local files
that can be uploaded; this is your section!

There are multiple ways of filling our datasets with data and actually, the steps don't differ much
from the upload-crawl-sync example.

- Crawl & Sync option: we can drop the data from the source to our dataset S3 bucket. Then, we will crawl and synchronize
data as we did in the previous steps 2 and 3.

- Register & Sync option: we drop the data from the source to our dataset S3 bucket. However, if we want to have more
control over our tables and its schema, instead of starting the crawler we can **register the tables** in the Glue
Catalog and then click on Synchronize as we did in step 3.

**How do we register Glue tables?** There are numerous ways:

- manually from the <a href="https://docs.aws.amazon.com/glue/latest/dg/console-tables.html">AWS Glue console</a> in your environment account
- Using <a href="https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api.html"> AWS Glue API</a>, `CreateTable`.
- In a Glue Job leveraging Glue <a href="https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-crawler-pyspark-extensions-dynamic-frame.html#aws-glue-api-crawler-pyspark-extensions-dynamic-frame-write"> PySpark DynamicFrame</a> class
- With <a href="https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/glue.html#Glue.Client.create_table">boto3</a>
- Or with <a href="https://github.com/awslabs/aws-data-wrangler">AWS Data Wrangler</a>, Pandas on AWS.
- Also, you can deploy Glue resources using <a href="https://docs.aws.amazon.com/glue/latest/dg/populate-with-cloudformation-templates.html">CloudFormation</a>
- Or directly, <a href="https://github.com/aws-samples/aws-glue-samples/tree/master/utilities/Hive_metastore_migration">migrating from Hive Metastore.</a>
- there are more for sure :)

!!! abstract "Use data.all pipelines to register Glue tables"
    data.all pipelines can be used to transform your data including the creation of Glue tables using
    <a href="https://docs.aws.amazon.com/glue/latest/dg/aws-glue-api-crawler-pyspark-extensions-dynamic-frame.html#aws-glue-api-crawler-pyspark-extensions-dynamic-frame-write"> AWS Glue pyspark extension </a>.
    Visit the <a href="pipelines.html">pipelines section</a> for more details.


### Folders

As previously defined, folders are prefixes inside our dataset S3 bucket. To create a folder, go to the **Data**
tab and on the folders section, click on Create. The following form will appear. 
We will dive deeper in how to use folders in the
<a href="tables.html">folders section</a>.

![create_folder](pictures/datasets/create_folder.png#zoom#shadow)

## :material-comment-text-multiple-outline: **Leave a message in Chat**
In the **Chats** button users can interact and leave their comments and questions on
the Dataset Chat.

![feed](pictures/datasets/dataset_feed.png#zoom#shadow)

## :material-tag-remove-outline: **Create key-value tags**
Same as in environments. In the **Tags** tab of the dataset window, we can create key-value tags.
These tags are not data.all tags
that are used to tag the dataset and find it in the catalog. In this case we are creating AWS tags as part of the
dataset CloudFormation stack. There are multiple tagging strategies as explained in the
<a href="https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html">documentation</a>.
