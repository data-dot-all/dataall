## **Tables**
In this section we will go through the different tabs in the Table window. We can reach this view:

1. by selecting a table from the data Catalog
2. or in the dataset view, in the **Tables** tab clicking on the arrow in the *Actions* column for the chosen table.

![](pictures/tables/table_dataset.png#zoom#shadow)

### :material-card-search-outline: **Check table metadata**
Also in the table window, go to the **Overview** tab where you will find the following information:

- URI: unique table identifier
- Name: name of the registered table in the Glue Catalog
- Tags
- Glossary terms
- Description
- Organization, Environment, Region, Team: inherited from the dataset
- Created: creation time of the table
- Status: `INSYNC`

!!! note "Description, Tags and Glossary terms are not inherited!"
    If a dataset is tagged with Tags and Glossary terms, the child tables do not inherit these tags and terms.
    In the Overview tab, by clicking on **Edit** is where you can add them. Same applies for the description.
    Adding tags and terms to your tables will make them more discoverable in the Catalog.

### :material-pencil-outline: **Add or edit table metadata**
Edit your table metadata by clicking on the **Edit** button.

### :material-eye-outline: **Preview data**
Data preview gives you the ability to preview a subset of the data available on data.all.
Preview feature is available for data you own or data that's shared with you.

Just select a table and in the **Preview** tab you will find the results of an SQL select subset of the table.

![](pictures/tables/table_preview.png#zoom#shadow)


### :material-comment-text-multiple-outline: **Leave a message in Chat**
As with datasets, in the **Chats** button users can interact and leave their comments and questions on
the Table Chat.

### :material-table-column-plus-before: **Add column description**
Metadata makes more sense when columns description fields are not empty.
With data.all you can add columns description and avoid the pain of figuring out fields purpose.

Select one table and in the **Columns** tab, directly type the description in the Description column
as shown in the picture.


![](pictures/tables/table_column.png#zoom#shadow)

###  :material-check-all: **Profile data**

Data profiling refers to the process of examining, analyzing,
and reviewing the data available in the source by collecting statistical information about the data set's quality and hygiene.
This process is called also data archaeology, data assessment, data discovery, or data quality analysis.
Data profiling helps in determining the accuracy, completeness, structure, and quality of your data.


Data profiling in data.all involves:

- Collecting descriptive statistics like minimum, maximum, mean, median, and standard deviation.
- Collecting data types, along with the minimum and maximum length.
- Determining the percentages of distinct or missing data.
- Identifying frequency distributions and significant values.


By selecting the **Metrics** tab of your data table you can run a profiling job (click in the **Profile** button)
, or view the latest generated data profiling metrics:

![](pictures/tables/table_metrics.png#zoom#shadow)

### :material-trash-can-outline: **Delete a table**
Deleting a table means deleting it from the data.all Catalog, but it will be still available on the AWS Glue Catalog.
Moreover, when data owners
delete a table, they are **not** deleting its data from the dataset S3 bucket. Teams with shared access to the dataset
cannot delete tables or folders, even if they are shared.

It is possible to delete a table from the dataset **Tables** tab with the trash can icon next to each of the
tables in the *Actions* column.

![](pictures/tables/table_delete.png#zoom#shadow)

Another option is to go to the specific table (on the above picture click on the arrow icon next to the trash can icon).
Click on the **Delete** button in the top right corner and confirm the deletion.

![](pictures/tables/table_delete_2.png#zoom#shadow)

!!! danger "An error occurred (ResourceShared) when calling DELETE_DATASET_TABLE operation: Revoke all table shares before deletion"
    To protect data consumers, if the table is shared you cannot delete it. The share requests to the table need to be
    revoked before deleting the table. Check the <a href="shares.html">Shares</a> section to learn how to grant and
    revoke access.

## **Folders**
To open the Folder window you can either find your chosen folder in the Catalog or navigate to the dataset and
then in the **Folders** tab click on the arrow in the *Actions* column of your folder:
![](pictures/tables/folder_1.png#zoom#shadow)


### :material-card-search-outline: **Check folder and S3 metadata**
The **Overview** tab of the folder contains folder metadata:
- URI: unique folder identifier
- Name: name of the folder, it is made out of the dataset name concatenated with the S3 prefix
- Tags
- Glossary terms
- Description
- Organization, Environment, Region, Team: inherited from the dataset
- Created: creation time of the table

![](pictures/tables/folder_2.png#zoom#shadow)

### :material-pencil-outline: **Add or edit table metadata**
Edit your folder metadata by clicking on the **Edit** button.

!!! note "Description, Tags and Glossary terms are not inherited"
    Careful, those 3 fields are not synced with their dataset metadata. Just click on
    the **Edit** button of the folder to complete any missing information. This is especially useful to
    improve Catalog search of your folders.

### :material-eye-outline: **Check the content of your folder**

To check what kind of files does our prefix content, we can access the AWS S3 console on the **S3 Bucket** button
of the Folder **Overview** tab.


![](pictures/tables/folder_3.png#zoom#shadow)

### :material-comment-text-multiple-outline: **Leave a message in Chat**
Exactly the same as with tables. Allow your teams to discuss directly on the Folder Chat.


### :material-trash-can-outline: **Delete a folder**
Deleting folders is analogous to deleting tables. Deletion means deletion from the data.all Catalog and the content
of the S3 prefix remains in the dataset S3 bucket. Only dataset owners can delete dataset folders.

The steps to delete a folder are exactly the same as with tables. You can either go to the dataset and in the
**Folders** tab click on the can trash icon on the *Actions* column of the selected folder; or you can navigate to the
Folder and click on the **Delete** button.

!!! danger "An error occurred (ResourceShared) when calling DELETE_DATASET_FOLDER operation: Revoke all folder shares before deletion"
    To protect data consumers, if the table is shared you cannot delete it. The share requests to the table need to be
    revoked before deleting the table. Check the <a href="shares.html">Shares</a> section to learn how to grant and
    revoke access.

![](pictures/tables/folder_delete.png#zoom#shadow)
