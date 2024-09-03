# **Redshift Datasets**

Data producers can now import their Redshift tables into data.all and make them discoverable and shareable in an easy
and secure manner.

In data.all we will work with 2 main constructs:
- **Redshift Connections**, which store the necessary metadata to connect to a Redshift namespace
- **Redshift Datasets**, group of tables imported into data.all Catalog using a data.all Redshift Connection.


## **Redshift Connections**

Data.all Redshift Connections are metadata used by data.all and by data.all users to connect to Redshift namespaces.
1) Both Redshift Serverless and Provisioned clusters are supported
2) Connections use AWS Secrets Manager secrets or Redshift users to connect to the namespace
3) There are 2 types of Redshift Connections, `ADMIN` and `DATA_USER`
    - `ADMIN` - the user whose credentials are provided has permissions to all namespace tables that can be managed in data.all and can create and manage Redshift datashares and redshift role permissions.
    - `DATA_USER` - the user whose credentials are provided has permissions to read the tables that the data user wants to import



**Pre-requisites**
Redshift clusters and users are typically managed by a dedicated team. For this reason, data.all will work "importing"
existing infrastructure and users:
- Redshift Serverless namespace/workgroup or Provisioned cluster: the user creating the connection must know the `namespace ID` and the `workgroup` for Redshift Serverless or the `cluster ID` for the case of Redshift Provisioned clusters. 
- Redshift user: Redshift administrators will manage the user creation.
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
| Connection name | Name of the Redshift connection                                                                                | Yes      | No       | Main cluster admin
| Connection type | Level of access of the connection. It can either be `ADMIN` or `DATA_USER`. See definitions above.             | Yes      | No       | `ADMIN`
| Team            | Team that owns the connection. This team is the only team that can use this connection to import datasets.     | Yes      | No       | DataScienceTeam
| Redshift type   | Type of Redshift Namespace. It can either be `serverless` or `cluster`.                                        | Yes      | No       | `serverless`
| Cluster Id      | If the Redshift type is `cluster`, we need to introduce the cluster Id.                                        | Yes      | No       | redshift-cluster-1
| Namespace Id    | If the Redshift type is `serverless`, we need to introduce the namespace Id.                                   | Yes      | No       | 0000000-0000-0000-0000-000000000000
| Workgroup       | If the Redshift type is `serverless`, we need to introduce the workgroup.                                      | Yes      | No       | workgroup1
| Database        | Database that we will connect to inside the cluster.                                                           | Yes      | No       | dev
| Redshift User   | Only available for `cluster` Redshift type. This is the user                                                   | Yes      | No       | `ADMIN`
| Secret Arn      | Secrets Manager secret arn storing username and password for the connection. See pre-requisites section above. | Yes      | Yes      | arn:aws:secretsmanager:eu-west-1:000000000000:secret:redshift!redshift-cluster-1-awsuser


Data.all will verify the connection upon creation. If the database does not exist or if the connection details are not accessible or do not 
correspond to cluster it will notify the user in the error banner.

**Delete a Connection**
To delete a connection, click on the trash icon next to the item in the Actions column. If the Connection has been used to import datasets it cannot be removed.

## :material-new-box: **Import a Redshift Dataset**
