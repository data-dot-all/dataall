# **Worksheets**

data.all offers a rich editor to write SQL queries and explore data. It is Athena on the backend that runs our queries
on environments where our teams have been onboarded.


## :material-new-box: **Create a Worksheet**
On the left pane under **Play** click on **Worksheets** to go to the Worksheet menu. Here you will find all
Worksheets owned by your teams.

!!! success "Shared queries = Seamless Collaboration"
    Check, learn from and collaborate with other members of your team to improve your analyses and get insights from
    your data, directly from data.all worksheets. No need to send queries by email, no need to create views :)


To create a new worksheet click on the **Create** button in the top right corner and fill the Worksheet form:

![worksheets](pictures/worksheets/ws_form.png#zoom#shadow)

| Field             | Description                                | Required | Editable |Example
|-------------------|--------------------------------------------|----------|----------|-------------
| Worksheet name    | Name of the worksheet                      | Yes      | Yes      |PalmDor
| Short description | Short description about the worksheet      | No       | Yes      |Query used to retrieve Palm D'or winners
| Team              | Team that owns the worksheet               | Yes      | No       |DataScienceTeam
| Tags              | Tags  | No       | Yes      |adhoc

!!! note "No AWS resources"
    When we are creating a worksheet we are NOT deploying AWS resources. We don't provision clusters, we are not creating
    tables or views. We simply store the query in data.all database and we run it serverlessly on AWS Athena.


## :material-pencil-outline: **Edit worksheet metadata**
Select a worksheet and click on the pencil icon to edit the metadata of the worksheet. This includes worksheet name,
description and tags. The ownership of the worksheet, its team, is not editable.

## :material-trash-can-outline: **Delete a worksheet**
Next to the edit button, there are 2 other buttons. To delete a worksheet click on the trash icon one. Worksheets
are not AWS resources, they are a data.all construct whose information is stored in the data.all database. Thus,
when we delete a worksheet we are not deleting AWS resources or CloudFormation stacks.

## :material-database-search: **Write and save your queries**
Select your worksheet and choose any of the environments, datasets and tables of your team to list column information.
In the query editor write your SQL statements and click on **Run Query** to get your query results. Error messages
coming from Athena will pop-up automatically.

![worksheets](pictures/worksheets/ws_joins.png#zoom#shadow)

If you want to save the current query for later or for other users, click on the **save** icon (next to the edit and the
delete buttons).

!!! success "More than just SELECT"
    Worksheets can be used for data exploration, for quick ad-hoc queries and for more complicated queries that require
    joins. As far as you have access to the joined datasets you can combine information from multiple tables or datasets.
    Check the <a href="https://docs.aws.amazon.com/athena/latest/ug/select.html" target="_blank">docs</a>
    for more information on AWS Athena SQL syntax.


## :material-new-box: **Experimental Features: GenAI Powered Worksheets**

As part of data.all >= v2.7 we introduced support for generative AI powered worksheet features. These features include both:

1. Natural Language Querying (NLQ) of Structured Data
2. Text Document Analysis of Unstructured Data

These features are optionally enabled/disabled via feature flags specified in data.all's configuration.

The More details on how to use each of these features are below.

### Natural Language Querying (NLQ) of Structured Data

data.all offers a NLQ feature to significantly redeuce the barrier for non-technical business users who need to quickly and easily query data to make informed decisions, as mastering these technical skills can be time-consuming.

The NLQ feature will take a user prompt and select number of tables and generate a ready to run SQL statement that data.all user's can execute against the data they have access to in data.all's Worksheets module.

To start generating SQL, data.all user's can select the TextToSQL Tab in the Worksheets View:

![worksheets_nlq](pictures/worksheets/ws_text_to_sql.png#zoom#shadow)


From their, user's will provide the environment, database, one or more tables to reference, and a user provided prompt. Behind the scenes' data.all will fetch the associated metadata for the table(s) the user selected, enrich the prompt with the additional metadata, and leverage genAI to generate a SQL statement that users can execute against their structured data.

Please note that the table metadata that data.all retrieves and enriches the user prompt to is subject to the same level of data access the user has in the data.all console. There are built in guardrails to ensure no mutating SQL statements (i.e. WRITE, UPSERT, DELETE, etc.) are generated against the data and to reduce hallucinations by ensuring the selected tables contain the correct data to answer the user's prompt.

data.all Admins can additionally limit the number of invocations run against these LLMs by specifying a `max_count_per_day` feature flag in data.all's configuration (please reference data.all's [Deployment Guide](https://data-dot-all.github.io/dataall/deploy-aws/#configjson) for more information)


### Text Document Analysis of Unstructured Data

For unstructured text documents, data.all offers a feature to start analyzing your data using natural language.

The Document Analyzer feature will take a user prompt and select S3 Object Key and generate a respwonse displayed in the data.all Worksheet Editor. 

!!! warning "Limitations of Document Analysis"
    Currently data.all's Worksheet Document Analyzer is limited only to `.txt` and `.pdf` file extensions. Additionally, the feature is limited only to 
    text documents which are explicitly owned by one of the user's teams (documents that are given access via data.all shares are not yet supported).


To start analyzing your text documents, data.all user's can select the Document Analyzer Tab in the Worksheets View:

![worksheets_unstructured](pictures/worksheets/ws_analyze_txt_doc.png#zoom#shadow)


From their, user's will provide the environment, S3 dataset bucket, S3 object key (from provided drop down), and a user provided prompt. Behind the scenes' data.all will fetch the content of the S3 Object and leverage genAI to generate a response with respect to the user's prompt about the text document.

There are built in guardrails to reduce hallucinations by ensuring the selected S3 Object contains infromation pertaining to the user's prompt.

data.all Admins can additionally limit the number of invocations run against these LLMs by specifying a `max_count_per_day` feature flag in data.all's configuration (please reference data.all's [Deployment Guide](https://data-dot-all.github.io/dataall/deploy-aws/#configjson) for more information)

