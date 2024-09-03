# **Redshift Datasets**

Data producers can now import their Redshift tables into data.all and make them discoverable and shareable in an easy
and secure manner.

In data.all we will work with 2 main constructs:
- **Redshift Connections**, which store the necessary metadata to connect to a Redshift namespace
- **Redshift Datasets**, group of tables imported into data.all Catalog using a data.all Redshift Connection.


## **Redshift Connections**

Data.all Redshift Connections are metadata used by data.all and by data.all users to connect to Redshift namespaces.
1) Both Redshift Serverless and Provisioned clusters are supported
2) Connections use AWS Secrets Manager secrets or Redshift users to connect to the namespace. Check the [documentation](https://docs.aws.amazon.com/redshift/latest/mgmt/query-editor-v2-using.html#query-editor-v2-connecting) to understand each mechanism. Additional connection mechanisms might be considered in the future.
3) There are 2 types of Redshift Connections, `ADMIN` and `DATA_USER`
    - `ADMIN` - the user whose credentials are provided has permissions to all namespace tables that can be managed in data.all and can create and manage Redshift datashares and redshift role permissions.
    - `DATA_USER` - the user whose credentials are provided has permissions to read the tables that the data user wants to import


**Pre-requisites**
Redshift clusters and users are typically managed by a dedicated team. For this reason, data.all will work "importing"
existing infrastructure and users:
- Redshift Serverless namespace/workgroup or Provisioned cluster: the user creating the connection must know the `namespace ID` and the `workgroup` for Redshift Serverless or the `cluster ID` for the case of Redshift Provisioned clusters. 
- Redshift user: Redshift administrators manage Redshift users outside of data.all. Our recommendation is to create a dedicated `ADMIN` user for data.all in each onboarded cluster. Data users can be reused.
- Connection details:
   - Redshift user: only valid for Provisioned clusters: 
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
| Redshift User   | Only available for `cluster` Redshift type. This is the user                                                   | Yes      | No       | TODO
| Secret Arn      | Secrets Manager secret arn storing username and password for the connection. See pre-requisites section above. | Yes      | Yes      | arn:aws:secretsmanager:eu-west-1:000000000000:secret:redshift!redshift-cluster-1-awsuser


Data.all will verify the connection upon creation. If the database does not exist or if the connection details are not accessible or do not 
correspond to cluster it will notify the user in the error banner.

**Delete a Connection**
To delete a connection, click on the trash icon next to the item in the Actions column. If the Connection has been used to import datasets it cannot be removed.

## :material-new-box: **Import a Redshift Dataset**
To create a new dataset, navigate to the Datasets view and click on **New Dataset**. A window like the one in the picture
will allow you to select the type of Dataset you want to create or import. In this case you need to select the Import
Redshift Dataset option.

![](pictures/redshift_datasets/redshift_dataset_creation.png#zoom#shadow)

Next, fill in the creation form with the Dataset details. Data.all will list the Redshift connections owned by the selected team in the environment
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

| Field                      | Description                                                       | Required | Editable |Example
|----------------------------|-------------------------------------------------------------------|----------|----------|-------------
| Redshift Connection        | Name of the Redshift connection used to read the Redshift tables  | Yes      | No       | main-cluster-userA
| Redshift database schema   | Name of the Redshift schema where the tables are stored           | Yes      | No       | public
| Redshift tables            | List of tables to be imported. They can be added at a later stage | No       | Yes      | customer, orders

## :material-card-search-outline: **Navigate dataset tabs**
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

![](pictures/redshift_datasets/redshift_add_tables.png#zoom#shadow)

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

## :material-pencil-outline: **Edit and update a dataset**
Data owners can edit the dataset by clicking on the **edit** button, editing the editable fields and saving the changes.

## :material-trash-can-outline: **Delete a dataset**
To delete a dataset, in the selected dataset window click on the **delete** button in the top-right corner. data.all Redshift 
Datasets don't deploy any CloudFormation stack, no additional resources need to be cleaned up. The original Redshift tables
will still exist in Redshift.