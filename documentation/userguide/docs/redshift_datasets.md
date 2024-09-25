# **Redshift Datasets**

Data producers can import their Redshift tables into data.all and make them discoverable and shareable in an easy
and secure manner.

In data.all we will work with 2 main constructs:

- **Redshift Connections**, which store the necessary metadata to connect to a Redshift namespace
- **Redshift Datasets**, group of tables imported into data.all Catalog using a data.all Redshift Connection.


## **Redshift Connections**

Data.all Redshift Connections are metadata used by data.all and by data.all users to connect to Redshift namespaces.

1) Both Redshift Serverless and Provisioned clusters are supported
2) Connections use AWS Secrets Manager secrets or Redshift users to connect to the namespace. Check the [documentation](https://docs.aws.amazon.com/redshift/latest/mgmt/query-editor-v2-using.html#query-editor-v2-connecting) to understand each mechanism. Additional connection mechanisms might be considered in the future.

### Connection Types

Here is a table to summarize the 2 different types of connections, keep reading to understand each type in depth.

| Connection type | Purpose in data.all             | Redshift permissions required | Grantable permissions 
|-----------------|---------------------------------|-------------------------------|--------------------
| `DATA_USER`     | Import Redshift Datasets        | READ Redshift tables          | None                          
| `ADMIN`         | Process Redshift share requests | MANAGE Redshift datashares    | `Use Connection in share request`


#### DATA USER Connections

`DATA_USER` connections are used to IMPORT Redshift dataset into data.all. The Redshift user used in the connection should have READ 
permissions to the tables to be imported. 

**Recommendations**

In the following example there are 2 teams, `ClusterAdminTeam` and `MarketingTeam`. Both have been onboarded to data.all
and can log in to the UI. The `ClusterAdminTeamA` is a team that administrates a Redshift cluster `RedshiftClusterA` in
the AWS Account of a data.all environment `EnvironmentA`. The `MarketingTeam` works in this cluster creating some tables `marketingTables`

It has been agreed that `marketingTables` should be imported to data.all. **Which type of connection should we use?** We need
to create a `DATA_USER` connection with a user that can read `marketingTables`. 

**And, which team should own the connection?** This depends on the data ownership requirements of your teams. The connection
owners will be able to import the Redshift dataset, becoming the dataset owners. The Redshift dataset
owners are in charge of managing the metadata of the dataset, editing/deleting and approving/revoking share requests.
If in your organization the `ClusterAdminTeamA` is in charge of managing all operations on the datasets then they should be 
the owners of the connection. If on the contrary, your organization has more distributed control over the operations on the 
data.all dataset, then the `MarketingTeam` should own the connection.

#### ADMIN Connections

`ADMIN` connections are used by data.all to process Redshift data share requests. The Redshift user used in the connection 
should have enough permissions to MANAGE DATASHARES in the cluster. 

**Recommendations**

We will continue the example of DATA_USER connections. Let's imagine that the `MarketingTeam` has happily imported the 
`marketingTables` Dataset and it is now published in the data.all Catalog. In another AWS Account `AccountB`, linked to
data.all as `EnvironmentB`, the `ResearchTeam` works in a Redshift cluster `RedshiftClusterB` managed by `ClusterAdminTeamB`. The 
`ResearchTeam` wants to request access to `marketingTables`. 

**Which type of connection should we use?** We need to create an `ADMIN` connection with a user that can manage Redshift 
datashares in both the `RedshiftClusterA` and `RedshiftClusterB`. 

**And, which team should own the connection?** The Connection owners should be teams with administrative
rights over the clusters. In this case the `ClusterAdminTeamA`
and `ClusterAdminTeamB` should own the `AdminConnectionA` and `AdminConnectionB` respectively.

**How can the `ResearchTeam` use the `AdminConnectionB`?** The `ClusterAdminTeamB` needs to grant "Use Connection in share request"
permissions for the connection `AdminConnectionB` to the `ResearchTeam`. After that the `ResearchTeam` will be able to
open share requests, but they won't be able to edit/delete the `AdminConnectionB`. The steps to grant these permissions
are explained in the Update Connection permissions subsection.



### Create a Redshift Connection

data.all requires Redshift clusters and users to be managed by a dedicated team and infrastructure created outside of data.all. 
For this reason, data.all will work "importing" existing infrastructure and users, requiring the following information on import:

- Redshift Serverless namespace/workgroup or Provisioned cluster: the user creating the connection must know the `namespace ID` and the `workgroup` for Redshift Serverless or the `cluster ID` for the case of Redshift Provisioned clusters. 
- Redshift user: Redshift administrators manage Redshift users outside of data.all. 
- Connection details:
   - Redshift user (only valid for Provisioned clusters): data.all will generate a temporary password to connect to the database. In this case no password or secret needs to be provided to data.all.
   - AWS Secrets Manager Secret (recommended): the username and password for the Redshift user can be stored in a Secret that **MUST** be tagged with 2 tags. Check the pictures below to see how it should look in the AWS Console.
       - tagKey: dataall, tagValue: True - Needed for data.all to be able to access the Secret
       - tagKey: Redshift, tagValue: Any - Needed by Redshift to use as connection

![](pictures/redshift_datasets/redshift_secret.png#zoom#shadow)

![](pictures/redshift_datasets/redshift_secret_tags.png#zoom#shadow)


Redshift Connections are created inside the Environment view. Select an Environment and navigate to the **Connections** tab.
Here you can click on the **Add Connection** button to create a new Redshift Connection.

![](pictures/redshift_datasets/redshift_connection_menu.png#zoom#shadow)

Then, fill in the following form:

![](pictures/redshift_datasets/redshift_connection_1.png#zoom#shadow)

| Field           | Description                                                                                                    | Required | Editable |Example
|-----------------|----------------------------------------------------------------------------------------------------------------|----------|----------|-------------
| Connection name | Name of the Redshift connection                                                                                | Yes      | No       | main-cluster-admin
| Connection type | Level of access of the connection. It can either be `ADMIN` or `DATA_USER`. See definitions above.             | Yes      | No       | `ADMIN`
| Team            | Team that owns the connection. This team is the only team that can use this connection to import datasets.     | Yes      | No       | DataScienceTeam
| Redshift type   | Type of Redshift Namespace. It can either be `serverless` or `cluster`.                                        | Yes      | No       | `serverless`
| Cluster Id      | If the Redshift type is `cluster`, we need to introduce the cluster Id.                                        | Yes      | No       | redshift-cluster-1
| Namespace Id    | If the Redshift type is `serverless`, we need to introduce the namespace Id.                                   | Yes      | No       | 0000000-0000-0000-0000-000000000000
| Workgroup       | If the Redshift type is `serverless`, we need to introduce the workgroup.                                      | Yes      | No       | workgroup1
| Database        | Database that we will connect to inside the cluster.                                                           | Yes      | No       | dev
| Redshift User   | Only available for `cluster` Redshift type. This is the user                                                   | Yes      | No       | user1
| Secret Arn      | Secrets Manager secret arn storing username and password for the connection. See pre-requisites section above. | Yes      | Yes      | arn:aws:secretsmanager:eu-west-1:000000000000:secret:redshift!redshift-cluster-1-awsuser


Data.all will verify the connection upon creation. If the database does not exist or if the connection details are not accessible or do not 
correspond to cluster it will notify the user in the error banner.

### Update Connection permissions
For `ADMIN` connections, the connection owners can grant additional permissions that allow other teams to use the 
connection. 

Navigate to ... TODO

### Delete a Connection
To delete a connection, click on the trash icon next to the item in the Actions column. If the Connection has been used 
to import datasets it cannot be removed until all associated datasets are deleted.

## :material-new-box: **Import a Redshift Dataset**
To create a new dataset, navigate to the Datasets view and click on **New Dataset**. A window like the one in the picture
will allow you to select the type of Dataset you want to create or import. In this case you need to select the Import
Redshift Dataset option.

![](pictures/redshift_datasets/redshift_dataset_creation.png#zoom#shadow)

Next, fill in the creation form with the Dataset details. To import Redshift Datasets, only connections of the type `DATA_USER` 
can be used. Therefore, data.all will list the Redshift `DATA_USER` connections owned by the selected team in the environment
and fetch the schemas and tables from Redshift. It is possible to select all tables or a subset of tables as appears in the picture.

![](pictures/redshift_datasets/redshift_dataset_creation_form.png#zoom#shadow)


**Generic dataset fields**

| Field                      | Description                                               | Required        | Editable |Example
|----------------------------|-----------------------------------------------------------|-----------------|----------|-------------
| Dataset name               | Name of the dataset                                       | Yes             | Yes      | AnyDataset
| Short description          | Short description about the dataset                       | No              | Yes      | For AnyProject predictive model
| Environment                | Environment (mapped to an AWS account)                    | Yes             | No       | DataScience
| Organization (auto-filled) | Organization of the environment                           | Yes             | No       | AnyCompany EMEA
| Team                       | Team that owns the dataset                                | Yes             | No       | DataScienceTeam
| Stewards                   | Team that can manage share requests on behalf of owners   | No              | Yes      | FinanceBITeam, FinanceMgmtTeam
| Confidentiality            | Level of confidentiality: Unclassified, Oficial or Secret | Yes             | Yes      | Secret
| Topics                     | Topics that can later be used in the Catalog              | Yes, at least 1 | Yes      | Finance
| Tags                       | Tags that can later be used in the Catalog                | Yes, at least 1 | Yes      | deleteme, ds
| Auto Approval              | Whether shares for this dataset need approval from dataset owners/stewards              | Yes (default `Disabled`) | Yes      | Disabled, Enabled

**Redshift Dataset fields**

| Field                      | Description                                                                                                                    | Required | Editable |Example
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------|----------|----------|-------------
| Redshift Connection        | Name of the Redshift connection used to read the Redshift tables. Only `DATA_USER` connections can be used to import Datasets. | Yes      | No       | main-cluster-userA
| Redshift database schema   | Name of the Redshift schema where the tables are stored                                                                        | Yes      | No       | public
| Redshift tables            | List of tables to be imported. They can be added at a later stage                                                              | No       | Yes      | customer, orders

Once a Redshift dataset has been imported, the dataset and its imported tables can be searched by any user in the Catalog. 

## :material-card-search-outline: **Navigate Redshift dataset tabs**
**Overview**

This tab includes meaningful metadata about the dataset and the Redshift connection used.

![](pictures/redshift_datasets/redshift_dataset_overview.png#zoom#shadow)

**Data**

This tab shows the Redshift database, schema and tables imported. From here we can add, edit, delete and see the details of a table.

![](pictures/redshift_datasets/redshift_dataset_data.png#zoom#shadow)

**Shares**
Show a list of the share requests for this Dataset. It is possible to verify the health and reapply shares for the
entire Dataset

### **Manage Redshift Tables**

**Add tables**

![](pictures/redshift_datasets/redshift_dataset_add_tables.png#zoom#shadow)

**View and edit tables**

We can view the schema of a table directly from the Data tab, by clicking on the **Open table schema** button.

![](pictures/redshift_datasets/redshift_schema.png#zoom#shadow)

We can also see a full view of the table by selecting the arrow in the Actions column. A new window for the table
will open. In this view we can edit the metadata of the table in data.all (Tags, glossary, description) and we can
see the schema in full-width in the Columns tab.

![](pictures/redshift_datasets/redshift_table.png#zoom#shadow)

**Delete a table**

We can delete Redshift tables by clicking on the trash icon next to the table we want to "un-import". Un-import is a better
word to describe what will happen: the metadata of the table will be deleted from data.all Catalog, but the original
Redshift table still exists in Redshift.

Dataset owners need to revoke access to the table before deleting. Data.all prevents deletion of a table if there are 
share requests currently sharing the table.

## :material-pencil-outline: **Edit and update a dataset**
Data owners can edit the dataset by clicking on the **edit** button, editing the editable fields and saving the changes.

## :material-trash-can-outline: **Delete a dataset**
To delete a dataset, in the selected dataset window click on the **delete** button in the top-right corner. data.all Redshift 
Datasets don't deploy any CloudFormation stack, no additional resources need to be cleaned up. The original Redshift tables
will still exist in Redshift.


In the same way as it happens with single tables, Dataset owners need to revoke access to all tables before deleting. 
Data.all prevents deletion of a dataset if there are 
share requests currently sharing any dataset table.