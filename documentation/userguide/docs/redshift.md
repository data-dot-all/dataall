# **Integrations**

## **Data Warehouse**
Datahub natively supports Amazon Redshift,
which allows you to integrate seamlessly your Redshift cluster with your Datahub environment.

### **Create Redshift cluster**

To create an Amazon Redshift cluster:

1. On left pane under **Play!** choose **Warehouses** then **Create**
2. The **creation form** opens.
3. Choose the environment where the cluster will
   be created.
4. Fill in the form with the cluster properties (The AWS VPC must have private subnets)
5. Save the form
![create_cluster](pictures/integrations/create_cluster.png#zoom#shadow)

!!! success
    **You created a new Amazon Redshift cluster!**

### **Import Redshift cluster**

If you already have data stored on Amazon S3 buckets, Datahub got you covered with the import feature.

To import a dataset:

1.  On left pane choose **Contribute** then **Import**
2.  The **dataset form** opens.
3.  Choose the environment where the dataset will
    be created.
4.  In **Dataset label**, enter a name for your dataset.
5.  Grab your Amazon S3 bucket name and put it on bucket name field.

![import_dataset](pictures/integrations/import_cluster.png#zoom#shadow)
!!! success
    **You imported an existing Redshift cluster to Datahub!**

### 📥 **Load datasets to your cluster with Spectrum**

Datahub offers natively an integration with Redshift Spectrum
to load your data from Amazon S3 to your cluster.
To load a dataset:

1. Select your Redshift cluster
2. Go to **Datasets** tab.
3. Click on **Load Datasets** and choose the dataset you want to load.
   ![load_dataset](pictures/integrations/load_dataset.png#zoom#shadow)
4. Use the connection details on the connection tab to access your cluster database
   ![connection](pictures/integrations/connection.png#zoom#shadow)
   ![connect_redshift](pictures/integrations/connect_redshift.png#zoom#shadow)
5. Query you dataset on Redshift.
   ![query_loaded_dataset](pictures/integrations/query_loaded_dataset.png#zoom#shadow)

### 🖨️ **Copy dataset table to your cluster with COPY command**
As data subscriber, Datahub can automate copying data from S3 to your Redshift cluster,
when data producers publish an update.

🧙 Load the dataset first, then manage its tables copy subscriptions.

To manage data copy:
1. Select your Redshift cluster
2. Go to **Tables** tab.
   ![enable_copy](pictures/integrations/enable_copy.png#zoom#shadow)
3. Click on **Subscribe** and choose the table you want to copy on the cluster and the target schema where
   the table will be created.
!!!abstract "COPY confirmed"
    Now your table will have the latest snapshot of data from the producers **at each update.**

The latest table data snapshot is created on the assigned schema
![copy_table.png](pictures/integrations/copy_table.png#zoom#shadow)
